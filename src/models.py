import datetime
from pydantic import BaseModel


class CityWeather(BaseModel):
    city_id: str
    temperature: float
    humidity: float


class Output(BaseModel):
    unique_id: str
    datetime: datetime.datetime
    response: list[CityWeather]
