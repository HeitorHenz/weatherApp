import pytest
from src.main import app, context
from src.utils import ProgressTracker, RateLimiter, Utils
from fastapi.testclient import TestClient

client = TestClient(app)


def test_rate_limiter():
    assert RateLimiter.get_calls()
    for i in range(RateLimiter.calls):
        RateLimiter.get_calls()
    assert RateLimiter.calls == 0
    assert not RateLimiter.get_calls()


def test_progress_tracker():
    cities = Utils.cities_list('static/test_cities.csv')
    assert len(cities) == 3
    pt = ProgressTracker('1', cities)
    assert not pt.finished
    assert len(pt.remaining_cities) == len(cities)
    cities_group = pt.get_cities_group()
    assert len(pt.remaining_cities) == 0
    assert len(pt.retrieved_cities) == 0
    pt.add_to_retrieved_cities(cities_group[:-1])
    assert len(pt.retrieved_cities) == (len(cities) - 1)
    assert '% done.' in pt.progress
    pt.retrieved_cities = []
    pt.retry_group(cities_group)
    assert pt.retries == 1
    cities_group = pt.get_cities_group()
    pt.add_to_retrieved_cities(cities_group)
    assert pt.finished


