import asyncio
import logging
import httpx
from datetime import datetime
from contextlib import asynccontextmanager
from .models import Output
from .settings import APISettings, DBSettings
from .utils import Utils, RateLimiter, ProgressTracker
from fastapi import FastAPI, HTTPException
import motor.motor_asyncio


cities = {}


# Loading the csv on startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    cities['list'] = Utils.cities_list()
    yield
    cities.clear()

app = FastAPI(lifespan=lifespan)
conn_string = DBSettings.get_connection()
client = motor.motor_asyncio.AsyncIOMotorClient(conn_string)
db = client['db']
collection = db['weather_data']
collection.create_index([("unique_id", 1)], unique=True)


@app.post('/data/{unique_id}', response_model=Output | str)
async def retrieve_cities_weather(unique_id: str):
    uid = await collection.find_one({'unique_id': unique_id})
    if ProgressTracker.get_ongoing_by_id(unique_id) or uid:
        err = f'Inputted id:{unique_id} is already registered. Please provide a valid unique_id'
        raise HTTPException(status_code=400, detail=err)
    pt = ProgressTracker(unique_id, cities['list'])
    request_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cities_data = []
    while not pt.finished:
        if RateLimiter.get_calls():
            logging.info(f"Sending request")
            async with httpx.AsyncClient() as client:
                cities_group = pt.get_cities_group()
                cg_args = ','.join(cities_group)
                r = await client.get(f'{APISettings.url()}{cg_args}')
                if r.status_code == 200:
                    pt.add_to_retrieved_cities(cities_group)
                    cities_data.extend(Utils.parse_response(r.text))
                    continue
                elif r.status_code == 404:
                    logging.warning('Check "static/cities.csv" before further tries')
                    err = 'No cities were given' if not cg_args else f'{r.text}'
                    raise HTTPException(
                        status_code=404,
                        detail=err
                    )
                else:
                    logging.info(f'Request failed with code {r.status_code}, retrying')
                    if pt.retries == APISettings.retry_cap:
                        logging.warning('Something unexpected happened, exiting')
                        raise HTTPException(status_code=r.status_code, detail=r.text)
                    pt.retry_group(cities_group)
                    continue
        else:
            logging.info('Out of requests at the moment, please wait')
            await asyncio.sleep(5)
            pass
    else:
        logging.info('Retrieval successful, finishing up')
        output_item = {
            'unique_id': unique_id,
            'datetime': request_datetime,
            'response': cities_data
        }
        await collection.insert_one(output_item)
        del pt
        return output_item


@app.get('/data/{unique_id}', response_model=str)
async def get_progress(unique_id: str):
    ongoing = ProgressTracker.get_ongoing_by_id(unique_id)
    if ongoing is not None:
        return ongoing.progress
    else:
        return f'There is no ongoing process with the unique id {unique_id}'


@app.get('/')
async def get_data():
    c = await collection.find().to_list(length=1000)
    out = []
    for e in c:
        e.pop('_id')
        out.append(e)
    return {'results': out}
