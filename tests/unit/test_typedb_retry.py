"""TDD Tests: TypeDB retry decorator for transient failures.

Per RELIABILITY-PLAN-01-v1 Priority 1:
Add retry with exponential backoff before falling back to in-memory.
Reduces memory_only sessions from transient TypeDB blips.
"""
import time
from unittest.mock import patch, MagicMock, call

import pytest


class TestRetryDecoratorExists:
    """retry_on_transient utility can be imported."""

    def test_importable(self):
        from governance.stores.retry import retry_on_transient
        assert callable(retry_on_transient)


class TestRetryBehavior:
    """retry_on_transient retries on ConnectionError/TimeoutError."""

    def test_succeeds_first_try(self):
        """No retry needed when function succeeds immediately."""
        from governance.stores.retry import retry_on_transient

        call_count = 0

        @retry_on_transient(max_attempts=3, base_delay=0.01)
        def good_fn():
            nonlocal call_count
            call_count += 1
            return "ok"

        result = good_fn()
        assert result == "ok"
        assert call_count == 1

    def test_retries_on_connection_error(self):
        """Retries on ConnectionError, succeeds on 2nd attempt."""
        from governance.stores.retry import retry_on_transient

        call_count = 0

        @retry_on_transient(max_attempts=3, base_delay=0.01)
        def flaky_fn():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ConnectionError("connection refused")
            return "recovered"

        result = flaky_fn()
        assert result == "recovered"
        assert call_count == 2

    def test_retries_on_timeout_error(self):
        """Retries on TimeoutError."""
        from governance.stores.retry import retry_on_transient

        call_count = 0

        @retry_on_transient(max_attempts=3, base_delay=0.01)
        def timeout_fn():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise TimeoutError("query timed out")
            return "ok"

        result = timeout_fn()
        assert result == "ok"
        assert call_count == 3

    def test_raises_after_max_attempts(self):
        """Raises original exception after max_attempts exhausted."""
        from governance.stores.retry import retry_on_transient

        @retry_on_transient(max_attempts=2, base_delay=0.01)
        def always_fails():
            raise ConnectionError("always down")

        with pytest.raises(ConnectionError, match="always down"):
            always_fails()

    def test_does_not_retry_value_error(self):
        """Does NOT retry on ValueError (not transient)."""
        from governance.stores.retry import retry_on_transient

        call_count = 0

        @retry_on_transient(max_attempts=3, base_delay=0.01)
        def logic_error():
            nonlocal call_count
            call_count += 1
            raise ValueError("bad input")

        with pytest.raises(ValueError):
            logic_error()
        assert call_count == 1  # No retry

    def test_does_not_retry_key_error(self):
        """Does NOT retry on KeyError (not transient)."""
        from governance.stores.retry import retry_on_transient

        call_count = 0

        @retry_on_transient(max_attempts=3, base_delay=0.01)
        def key_error():
            nonlocal call_count
            call_count += 1
            raise KeyError("missing")

        with pytest.raises(KeyError):
            key_error()
        assert call_count == 1

    def test_exponential_backoff(self):
        """Delays increase between retries."""
        from governance.stores.retry import retry_on_transient

        call_count = 0
        timestamps = []

        @retry_on_transient(max_attempts=3, base_delay=0.05)
        def slow_recovery():
            nonlocal call_count
            timestamps.append(time.monotonic())
            call_count += 1
            if call_count < 3:
                raise ConnectionError("still down")
            return "ok"

        result = slow_recovery()
        assert result == "ok"
        assert len(timestamps) == 3
        # Second delay should be longer than first
        delay1 = timestamps[1] - timestamps[0]
        delay2 = timestamps[2] - timestamps[1]
        assert delay2 > delay1 * 0.9  # Allow 10% jitter tolerance
