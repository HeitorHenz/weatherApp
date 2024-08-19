import asyncio
import logging
import httpx
from datetime import datetime
from typing import Annotated
from .models import Output
from .settings import APISettings, DBSettings
from .utils import Utils, RateLimiter, ProgressTracker
from fastapi import Depends, FastAPI, HTTPException
import motor.motor_asyncio


async def context():
    input_path = 'static/cities.csv'
    db_name = 'db'
    collection_name = 'weather_data'
    client = motor.motor_asyncio.AsyncIOMotorClient(DBSettings.get_connection())
    db = client[db_name]
    collection = db[collection_name]
    await collection.create_index([("unique_id", 1)], unique=True)

    return {
        'input': Utils.cities_list(input_path),
        'collection': collection
    }


app = FastAPI()


@app.post('/data/{unique_id}', response_model=Output | str)
async def retrieve_cities_weather(unique_id: str, data: Annotated[dict, Depends(context)]):
    uid = await data['collection'].find_one({'unique_id': unique_id})
    if ProgressTracker.get_ongoing_by_id(unique_id) or uid:
        err = f'Inputted id:{unique_id} is already registered. Please provide a valid unique_id'
        raise HTTPException(status_code=400, detail=err)
    pt = ProgressTracker(unique_id, data['input'])

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
        await data['collection'].insert_one(output_item)
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
async def get_data(data: Annotated[dict, Depends(context)]):
    c = await data['collection'].find().to_list(length=1000)
    out = []
    for e in c:
        e.pop('_id')
        out.append(e)
    return {'results': out}
