import os

from sqlalchemy import URL

from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, AsyncSession, create_async_engine, AsyncEngine
from sqlalchemy.orm import DeclarativeBase

DB_URL = URL.create(
            'postgresql+asyncpg',
            username=os.getenv('db_user'),
            password=os.getenv('db_password'),
            port=os.getenv('db_port'),
            host='localhost',
            database=os.getenv('db_name')
        )

ENGINE = create_async_engine(
            DB_URL, echo=True, pool_pre_ping=True,
        )


class Base(AsyncAttrs, DeclarativeBase):
    pass


async def proceed_schemas(engine: AsyncEngine) -> None:
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)


async def drop_all_tables(engine: AsyncEngine) -> None:
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)


def get_session_maker(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(
        engine, expire_on_commit=False, autocommit=False
        )
