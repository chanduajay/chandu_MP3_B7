# utils/decorators.py
"""
Reusable decorators used across all service modules.

@log_call  — logs entry and exit of every decorated function.
@retry     — retries a function up to `times` attempts before re-raising.
"""

import functools
import time
import logging


def log_call(func):
    """Log function name before and after execution."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logging.info(f"Calling {func.__name__}")
        result = func(*args, **kwargs)
        logging.info(f"{func.__name__} completed")
        return result
    return wrapper


def retry(times=3, delay=1):
    """
    Retry a function up to `times` attempts with `delay` seconds between tries.
    Re-raises the last exception if all attempts fail.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(1, times + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    logging.warning(
                        f"[retry] {func.__name__} attempt {attempt}/{times} failed: {e}"
                    )
                    if attempt == times:
                        raise
                    time.sleep(delay)
        return wrapper
    return decorator
