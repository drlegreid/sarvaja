"""
Retry decorator for transient TypeDB failures.

Per RELIABILITY-PLAN-01-v1 Priority 1:
Retries on ConnectionError/TimeoutError with exponential backoff
before falling back to in-memory stores.
"""

import functools
import logging
import time

logger = logging.getLogger(__name__)

# Exception types considered transient (worth retrying)
# BUG-196-021: Include RuntimeError — _execute_query raises it on disconnect
# BUG-241-RET-001: Filter RuntimeError to connection-related messages only
class _TransientRuntimeError(RuntimeError):
    """Marker subclass — never raised directly; used for isinstance matching."""
    pass


def _is_transient(exc: Exception) -> bool:
    """Check if exception is transient (worth retrying).

    BUG-340-RETRY-001: Filter OSError by errno — PermissionError, FileNotFoundError,
    and other non-transient OS errors should NOT be retried.
    """
    if isinstance(exc, (ConnectionError, TimeoutError)):
        return True
    if isinstance(exc, OSError):
        # Only retry on connection-related errno codes
        import errno
        _TRANSIENT_ERRNOS = {
            errno.ECONNREFUSED, errno.ECONNRESET, errno.ECONNABORTED,
            errno.ETIMEDOUT, errno.EHOSTUNREACH, errno.ENETUNREACH,
        }
        return getattr(exc, 'errno', None) in _TRANSIENT_ERRNOS
    if isinstance(exc, RuntimeError):
        msg = str(exc).lower()
        return any(kw in msg for kw in ("disconnect", "connection", "unavailable", "closed"))
    return False


TRANSIENT_EXCEPTIONS = (ConnectionError, TimeoutError, OSError, RuntimeError)


def retry_on_transient(max_attempts: int = 2, base_delay: float = 0.5):
    """
    Decorator that retries a function on transient failures.

    Args:
        max_attempts: Maximum number of attempts (default 2).
        base_delay: Base delay in seconds between retries (doubles each attempt).

    Only retries on TRANSIENT_EXCEPTIONS. Non-transient errors
    (ValueError, KeyError, etc.) are raised immediately.
    """
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            last_exc = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return fn(*args, **kwargs)
                except TRANSIENT_EXCEPTIONS as e:
                    # BUG-241-RET-001: Use _is_transient filter for RuntimeError
                    if not _is_transient(e):
                        raise
                    last_exc = e
                    if attempt < max_attempts:
                        delay = base_delay * (2 ** (attempt - 1))
                        logger.warning(
                            f"Transient error in {fn.__name__} (attempt {attempt}/{max_attempts}): {e}. "
                            f"Retrying in {delay:.2f}s..."
                        )
                        time.sleep(delay)
                    else:
                        logger.error(
                            f"Transient error in {fn.__name__} after {max_attempts} attempts: {e}"
                        )
            raise last_exc
        return wrapper
    return decorator
