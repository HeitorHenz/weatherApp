import os
from dotenv import load_dotenv


class APISettings:
    base_url = 'https://api.openweathermap.org/data/2.5/group?units=metric'
    interval = 60  # Time needed for making new API calls(in seconds)
    interval_cap = 60  # Maximum number of cities requested in an interval
    group_cap = 20  # Maximum number of cities in a single group request
    retry_cap = 3  # Maximum number of retries in case of a timeout/unforeseen error

    @staticmethod
    def get_key() -> str:
        load_dotenv()
        if not os.getenv('API_KEY'):
            raise KeyError('API_KEY environment variable not set')
        else:
            return os.getenv('API_KEY')

    @classmethod
    def url(cls) -> str:
        return f'{cls.base_url}&appid={cls.get_key()}&id='


class DBSettings:
    host = 'localhost'
    port = '27017'

    @classmethod
    def get_connection(cls) -> str:
        load_dotenv()
        if not os.getenv('MONGO_INITDB_ROOT_USERNAME'):
            raise KeyError('MONGO_INITDB_ROOT_USERNAME environment variable not set')
        elif not os.getenv('MONGO_INITDB_ROOT_PASSWORD'):
            raise KeyError('MONGO_INITDB_ROOT_PASSWORD environment variable not set')
        else:
            user = os.getenv('MONGO_INITDB_ROOT_USERNAME')
            password = os.getenv('MONGO_INITDB_ROOT_PASSWORD')
            return f'mongodb://{user}:{password}@{cls.host}:{cls.port}'
