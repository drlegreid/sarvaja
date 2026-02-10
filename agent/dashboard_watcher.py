"""
Dashboard File Watcher - Auto-restart Trame on agent/ code changes.

Per GAP-WORKFLOW-RELOAD-001: Dashboard Trame has no hot-reload.
API uses uvicorn --reload, but Trame caches Python modules at startup.
This watcher monitors /app/agent for .py file changes and restarts the process.

Created: 2026-02-08
"""

import os
import sys
import signal
import subprocess
import time
import logging
from watchdog.observers.polling import PollingObserver as Observer
from watchdog.events import FileSystemEventHandler

logging.basicConfig(level=logging.INFO, format="[dashboard-watcher] %(message)s")
logger = logging.getLogger(__name__)

DEBOUNCE_SECONDS = 2.0
POLL_INTERVAL = 3  # seconds between polling checks (for bind-mount compatibility)


class DashboardReloader(FileSystemEventHandler):
    """Restart dashboard process on Python file changes."""

    def __init__(self, process_args: list[str]):
        self.process_args = process_args
        self.process: subprocess.Popen | None = None
        self._last_event_time = 0.0

    def start_process(self) -> None:
        """Start the dashboard subprocess."""
        if self.process and self.process.poll() is None:
            logger.info("Stopping old dashboard process (pid=%d)...", self.process.pid)
            self.process.send_signal(signal.SIGTERM)
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()

        logger.info("Starting dashboard: %s", " ".join(self.process_args))
        self.process = subprocess.Popen(self.process_args)

    def on_modified(self, event):
        self._handle_change(event)

    def on_created(self, event):
        self._handle_change(event)

    def _handle_change(self, event):
        if event.is_directory:
            return
        if not event.src_path.endswith(".py"):
            return

        now = time.monotonic()
        if now - self._last_event_time < DEBOUNCE_SECONDS:
            return
        self._last_event_time = now

        rel_path = os.path.relpath(event.src_path, "/app")
        logger.info("File changed: %s — restarting dashboard...", rel_path)
        self.start_process()


def main():
    port = os.environ.get("DASHBOARD_PORT", "8081")
    dashboard_cmd = [
        sys.executable, "-m", "agent.governance_dashboard",
        "--port", port,
    ]

    reloader = DashboardReloader(dashboard_cmd)
    reloader.start_process()

    observer = Observer(timeout=POLL_INTERVAL)
    watch_dirs = ["/app/agent", "/app/governance"]
    for d in watch_dirs:
        if os.path.isdir(d):
            observer.schedule(reloader, d, recursive=True)
            logger.info("Watching %s for changes (polling, interval=%ss)", d, POLL_INTERVAL)

    observer.start()
    logger.info("Dashboard watcher active (polling, debounce=%ss)", DEBOUNCE_SECONDS)

    try:
        while True:
            if reloader.process and reloader.process.poll() is not None:
                exit_code = reloader.process.returncode
                logger.warning("Dashboard exited with code %d, restarting...", exit_code)
                time.sleep(1)
                reloader.start_process()
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down watcher...")
    finally:
        observer.stop()
        observer.join()
        if reloader.process and reloader.process.poll() is None:
            reloader.process.terminate()
            reloader.process.wait(timeout=5)


if __name__ == "__main__":
    main()
