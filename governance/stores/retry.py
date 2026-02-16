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
TRANSIENT_EXCEPTIONS = (ConnectionError, TimeoutError, OSError)


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
