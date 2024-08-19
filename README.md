# WeatherApp


App for consuming and storing [OpenWeatherMap](https://openweathermap.org) data, compliant with free plan limits.\
Despite still being available, the endpoint used(`https://api.openweathermap.org/data/2.5/group?`) is no longer on the documentation. However, it may be found at:\
<https://web.archive.org/web/20210122004654/https://openweathermap.org/current#severalid>.

***
## How to run

Run `docker compose up --build -d` at the root directory
***
## Usage

All endpoints can be accessed at <localhost:9999/docs> by default.

#### Endpoints

*Retrieve Cities Weather*: Retrieves the data from OWM api and stores it in a MongoDB database\
*Get Progress*: Receives an ID and shows the current progress of *Retrieve Cities Weather* if it matches an ongoing request\
*Get Data*: Returns all objects from the database.

An API key, as well as your choice of user/password for the database must be provided in the `.env` file located at the root directory.\
The application uses a single line csv as input, provided already populated at `static/cities.csv`\
Each comma separated value must contain a `City ID`.
As is the case with the `?group` endpoint, further id's can only be found with web.archive, at:\
<http://web.archive.org/web/20180619015316/http://openweathermap.org/help/city_list.txt>.

Additional customisation can be achieved by editing the `settings.py` file.

## Testing

Run `docker compose exec api python3 -m pytest --cov-report term --cov=src`

## Reasoning behind the stack
*FastAPI* and it's dependencies(such as pydantic) make for a great starting point for an async application,
while also providing automatic documentation for ease of use.\
*httpx* was already used as a dependency for FastAPI testing, so it was an adequate choice for making async calls.\
*MongoDB* was chosen as a easy way to store the json output.