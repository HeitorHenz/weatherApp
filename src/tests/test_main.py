import asyncio
import json
import motor.motor_asyncio
import pytest
from src.main import app, context
from src.utils import Utils
from httpx import AsyncClient
from src.settings import DBSettings


input_path = 'static/test_cities.csv'
db_name = 'test_db'
collection_name = 'test_collection'
input_csv = Utils.cities_list(input_path)


@pytest.fixture
def anyio_backend():
    return 'asyncio'


async def override_context():
    client = motor.motor_asyncio.AsyncIOMotorClient(DBSettings.get_connection())
    client.get_io_loop = asyncio.get_running_loop
    db = client[db_name]
    collection = db[collection_name]
    await collection.create_index([("unique_id", 1)], unique=True)
    return {
        'input': input_csv,
        'db': db,
        'collection': collection
    }


async def override_context_no_input():
    client = motor.motor_asyncio.AsyncIOMotorClient(DBSettings.get_connection())
    client.get_io_loop = asyncio.get_running_loop
    db = client[db_name]
    collection = db[collection_name]
    await collection.create_index([("unique_id", 1)], unique=True)
    return {
        'input': [],
        'db': db,
        'collection': collection
    }


@pytest.mark.anyio
async def test_context():
    c = await context()
    assert type(c['input']) is list


app.dependency_overrides[context] = override_context


@pytest.mark.anyio
async def test_get_progress_no_process():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/data/1")
        assert response.status_code == 200
        assert 'no ongoing process' in response.text


@pytest.mark.anyio
async def test_retrieve_cities_weather():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/data/1")
        assert response.status_code == 200
        assert len(json.loads(response.text)['response']) == 3


@pytest.mark.anyio
async def test_retrieve_cities_weather_dup_id():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/data/1")
        assert response.status_code == 400


@pytest.mark.anyio
async def test_get_data():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/")
        assert response.status_code == 200
        assert len(json.loads(response.text)['results']) == 1


@pytest.mark.anyio
async def test_retrieve_cities_weather_no_input():
    app.dependency_overrides[context] = override_context_no_input
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/data/2")
        assert response.status_code == 404


@pytest.mark.anyio
async def test_cleanup():
    client = motor.motor_asyncio.AsyncIOMotorClient(DBSettings.get_connection())
    db = client['test_db']
    await db.drop_collection('test_collection')
    app.dependency_overrides = {}
