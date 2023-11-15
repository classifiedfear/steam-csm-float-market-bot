import time
from functools import wraps

import pytest

from telegram_bot.resources.misc import ClosableQueue


@pytest.fixture
def queue():
    return ClosableQueue()


def time_checker(func):
    @wraps(func)
    async def wrapper_decorator(*args, **kwargs):
        s = time.perf_counter()
        data = await func(*args, **kwargs)
        elapsed = time.perf_counter() - s
        print(f"{__file__} executed in {elapsed:0.2f} seconds.")
        return data
    return wrapper_decorator
