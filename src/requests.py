import ssl
import gzip
import json
import time
import random
import http.client
import socket
import zlib
from io import BytesIO
from functools import wraps
from typing import Optional, Tuple
from src import info, silent_error, error


class HTTPException(Exception):
    pass

class RateLimitException(HTTPException):
    pass

# Retry conditions and strategies
def stop_after_custom_attempts(attempt_number):
    return attempt_number >= 5

def stop_never(attempt_number):
    return False

def wait_random_exponential(attempt_number, multiplier=1, max_wait=10):
    return min(multiplier * (2 ** random.uniform(0, attempt_number - 1)), max_wait)

def retry_if_exception_type(exceptions):
    return lambda e: isinstance(e, exceptions)

def retry(stop=None, wait=None, retry=None, after=None, before_sleep=None):
    """Retry decorator with custom stop, wait, and retry conditions."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempt_number = 0
            while True:
                try:
                    attempt_number += 1
                    return func(*args, **kwargs)
                except Exception as e:
                    if retry and not retry(e):
                        raise
                    if after:
                        after({'attempt_number': attempt_number, 'outcome': e})
                    # Apply different stop conditions based on exception type
                    if stop and stop(e, attempt_number):
                        raise
                    if before_sleep:
                        before_sleep({'attempt_number': attempt_number})
                    wait_time = wait(attempt_number) if wait else 1
                    time.sleep(wait_time)
        return wrapper
    return decorator

# Custom stop condition that handles RateLimitException and other exceptions separately
def custom_stop_condition(exception, attempt_number):
    if isinstance(exception, RateLimitException):
        return False
    return stop_after_custom_attempts(attempt_number)

# Retry configuration:
retry_config = {
    'stop': custom_stop_condition,
    'wait': lambda attempt_number: wait_random_exponential(
        attempt_number, multiplier=1, max_wait=10
    ),
    'retry': retry_if_exception_type((HTTPException,)),
    'before_sleep': lambda retry_state: info(
        f"Sleeping before next retry ({retry_state['attempt_number']})"
    )
}

class RateLimiter:
    def __init__(self, interval: float = 1):
        self.interval = interval
        self.timestamp = time.time()

    def wait_for_next_request(self):
        now = time.time()
        elapsed = now - self.timestamp
        sleep_time = max(0, self.interval - elapsed)
        if sleep_time > 0:
            time.sleep(sleep_time)
        self.timestamp = time.time()

def rate_limited_request(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        rate_limiter = RateLimiter()
        rate_limiter.wait_for_next_request()
        return func(*args, **kwargs)
    return wrapper
