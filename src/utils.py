import csv
import time
import json
from copy import deepcopy
from .settings import APISettings


class Utils:
    @staticmethod
    def cities_list(path: str = 'static/cities.csv') -> list[str]:
        with open(path) as f:
            return next(csv.reader(f))

    @staticmethod
    def parse_response(response: str) -> list[dict]:
        r_data = json.loads(response)['list']
        parsed_data = []
        for city in r_data:
            parsed_data.append({
                'city_id': str(city['id']),
                'temperature': city['main']['temp'],
                'humidity': city['main']['humidity']
            })
        return parsed_data


# Implementation of a token bucket-like algorithm
class RateLimiter:
    max_calls = APISettings.interval_cap // APISettings.group_cap
    time_limit = APISettings.interval
    calls = max_calls
    start_time = time.perf_counter()

    @classmethod
    def get_calls(cls) -> bool:
        if cls.calls < 1 and not cls.refresh_calls():
            return False
        else:
            cls.calls -= 1
            return True

    @classmethod
    def refresh_calls(cls) -> bool:
        now_time = time.perf_counter()
        elapsed_time = now_time - cls.start_time
        if elapsed_time < cls.time_limit:
            return False
        cls.calls = cls.max_calls
        cls.start_time = now_time
        return True


class ProgressTracker:
    ongoing_requests = []

    def __init__(self, unique_id: str, cities: list[str]):
        self.unique_id = unique_id
        self.total_cities = len(cities)
        self.remaining_cities = deepcopy(cities)
        self.retrieved_cities = []
        self.retries = 0
        ProgressTracker.ongoing_requests.append(self)

    def __str__(self):
        return f'id:{self.unique_id}'

    @property
    def finished(self) -> bool:
        if len(self.retrieved_cities) == self.total_cities and self.total_cities != 0:
            ProgressTracker.ongoing_requests.remove(self)
            return True
        return False

    @property
    def progress(self) -> str:
        p = len(self.retrieved_cities) / self.total_cities * 100
        return f'unique_id: {self.unique_id} is {p:.2f}% done.'

    def get_cities_group(self) -> list:
        group = self.remaining_cities[:APISettings.group_cap]
        self.remaining_cities = [rc for rc in self.remaining_cities if rc not in group]
        return group

    def add_to_retrieved_cities(self, group: list[str]) -> None:
        self.retrieved_cities.extend(group)
        return

    def retry_group(self, group: list[str]) -> None:
        self.remaining_cities.extend(group)
        self.retries += 1
        return

    @classmethod
    def get_ongoing_by_id(cls, ongoing_id: str):
        return next(filter(lambda o: o.unique_id == ongoing_id, cls.ongoing_requests), None)
