import os
import tempfile

import pytest
from backd.utils import caching


@pytest.fixture
def dummy_func():
    def func(n):
        func.call_count += 1
        return n + 1

    func.call_count = 0
    return func


@pytest.fixture
def temp_dir():
    directory = tempfile.TemporaryDirectory(prefix="backd-")
    yield directory
    directory.cleanup()


def test_cache_too_short(temp_dir, dummy_func):
    decorated = caching.cache(
        ttl=10, min_memory_time=1, min_disk_time=1, directory=temp_dir.name
    )(dummy_func)
    assert decorated(1) == 2
    assert dummy_func.call_count == 1
    assert os.listdir(temp_dir.name) == []
    assert decorated(1) == 2
    assert dummy_func.call_count == 2


def test_cache_memory_caching(temp_dir, dummy_func):
    decorated = caching.cache(
        ttl=10, min_memory_time=0, min_disk_time=1, directory=temp_dir.name
    )(dummy_func)
    assert decorated(2) == 3
    assert len(os.listdir(temp_dir.name)) == 0
    assert dummy_func.call_count == 1
    assert decorated(2) == 3
    assert len(os.listdir(temp_dir.name)) == 0
    assert dummy_func.call_count == 1
    assert decorated(3) == 4
    assert len(os.listdir(temp_dir.name)) == 0
    assert dummy_func.call_count == 2


def test_memory_pickle_caching_ttl(temp_dir, dummy_func):
    decorated = caching.cache(
        ttl=0, min_memory_time=0, min_disk_time=1, directory=temp_dir.name
    )(dummy_func)
    assert decorated(2) == 3
    assert dummy_func.call_count == 1
    assert decorated(2) == 3
    assert dummy_func.call_count == 2
    assert len(os.listdir(temp_dir.name)) == 0


def test_cache_memory_caching_negative_ttl(temp_dir, dummy_func):
    decorated = caching.cache(
        ttl=-1, min_memory_time=0, min_disk_time=1, directory=temp_dir.name
    )(dummy_func)
    assert decorated(2) == 3
    assert dummy_func.call_count == 1
    assert decorated(2) == 3
    assert dummy_func.call_count == 1


def test_cache_pickle_caching(temp_dir, dummy_func):
    decorated = caching.cache(
        ttl=10, min_memory_time=1, min_disk_time=0, directory=temp_dir.name
    )(dummy_func)
    assert decorated(2) == 3
    assert len(os.listdir(temp_dir.name)) == 1
    assert dummy_func.call_count == 1
    assert decorated(2) == 3
    assert len(os.listdir(temp_dir.name)) == 1
    assert dummy_func.call_count == 1
    assert decorated(3) == 4
    assert len(os.listdir(temp_dir.name)) == 2
    assert dummy_func.call_count == 2


def test_cache_pickle_caching_ttl(temp_dir, dummy_func):
    decorated = caching.cache(
        ttl=0, min_memory_time=1, min_disk_time=0, directory=temp_dir.name
    )(dummy_func)
    assert decorated(2) == 3
    assert dummy_func.call_count == 1
    assert decorated(2) == 3
    assert dummy_func.call_count == 2


def test_cache_pickle_caching_negative_ttl(temp_dir, dummy_func):
    decorated = caching.cache(
        ttl=-1, min_memory_time=1, min_disk_time=0, directory=temp_dir.name
    )(dummy_func)
    assert decorated(2) == 3
    assert dummy_func.call_count == 1
    assert decorated(2) == 3
    assert dummy_func.call_count == 1


def test_should_cache_true(temp_dir, dummy_func):
    decorated = caching.cache(
        ttl=10,
        min_memory_time=0,
        min_disk_time=1,
        directory=temp_dir.name,
        should_cache=lambda _res, _arg: True,
    )(dummy_func)
    assert decorated(2) == 3
    assert dummy_func.call_count == 1
    assert decorated(2) == 3
    assert dummy_func.call_count == 1


def test_should_cache_false(temp_dir, dummy_func):
    decorated = caching.cache(
        ttl=10,
        min_memory_time=0,
        min_disk_time=1,
        directory=temp_dir.name,
        should_cache=lambda _, n: n == 0,
    )(dummy_func)
    assert decorated(2) == 3
    assert dummy_func.call_count == 1
    assert decorated(2) == 3
    assert dummy_func.call_count == 2
