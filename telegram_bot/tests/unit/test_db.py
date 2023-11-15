import asyncio
import os

import pytest
import pytest_asyncio

from sqlalchemy import URL
from sqlalchemy.ext.asyncio import create_async_engine

from telegram_bot.db.base import proceed_schemas, get_session_maker, drop_all_tables
from telegram_bot.db import db_query

pytestmark = pytest.mark.asyncio


@pytest.fixture(scope="session")
def event_loop(request):
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope='session', autouse=True)
async def session_maker():
    url = URL.create(
            'postgresql+asyncpg',
            username=os.getenv('db_user'),
            password=os.getenv('db_password'),
            port=os.getenv('db_port'),
            host='localhost'
        )
    engine = create_async_engine(
            url, echo=True, pool_pre_ping=True,
        )
    await proceed_schemas(engine)

    await db_query.add_new_skin_to_db(
        get_session_maker(engine),
        'USP-S',
        'Cortex',
        False,
        'Factory New', 'Minimal Wear'
    )
    yield get_session_maker(engine)
    await drop_all_tables(engine)


async def test_db_add_new_user(session_maker):
    await db_query.add_user(session_maker, 1, 'classified', 'Igor Annenko')
    data = await db_query.is_user_exists(session_maker, 1,)
    assert data is True


async def test_db_remove_user(session_maker):
    await db_query.remove_user(session_maker, 1)
    data = await db_query.is_user_exists(session_maker, 1)
    assert data is False


@pytest.mark.parametrize(('weapon_data', 'result'), [
        (
                {
                    'weapon': 'Desert Eagle',
                    'skin': 'Code Red',
                    'quality': 'Well-Worn',
                    'stattrak': True
                },
                ('Code Red', 'Desert Eagle', 'Well-Worn', True)
        )]
        )
async def test_should_add_new_skin(weapon_data, result, session_maker):
    await db_query.add_new_skin_to_db(
        session_maker,
        weapon_data['weapon'],
        weapon_data['skin'],
        weapon_data['stattrak'], *(
            'Factory New', 'Minimal Wear', 'Field-Tested', 'Well-Worn', 'Battle-Scarred'
        ))
    data = await db_query.is_skin_exists(
        session_maker, weapon_data['weapon'], weapon_data['skin'], weapon_data['quality'], weapon_data['stattrak']
    )
    assert data == result


@pytest.mark.parametrize(
    ('weapon_data', 'result'),
    [
        (
                {
                    'weapon': 'USP-S',
                    'skin': 'Cortex',
                    'quality': 'Factory New',
                    'stattrak': False
                },
                ('Cortex', 'USP-S', 'Factory New', False)
        ),

        (
                {
                    'weapon': 'AK-47',
                    'skin': 'Asiimov',
                    'quality': 'Field-Tested',
                    'stattrak': False
                },
                None
        ),

        (
                {
                    'weapon': 'Desert Eagle',
                    'skin': 'Code Red',
                    'quality': 'Well-Worn',
                    'stattrak': True
                },
                ('Code Red', 'Desert Eagle', 'Well-Worn', True)
        )
    ]
)
async def test_db_check_if_skin_exists(weapon_data, result, session_maker):
    data = await db_query.is_skin_exists(
        session_maker, weapon_data['weapon'], weapon_data['skin'], weapon_data['quality'], weapon_data['stattrak'])
    assert data == result


async def test_should_give_all_users(session_maker):
    for user in await db_query.get_users(session_maker):
        assert user.user_id == 1





