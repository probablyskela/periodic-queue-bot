import typing
from contextlib import asynccontextmanager

from redis.asyncio import Redis as AsyncRedis
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import config
from app.database import Session
from app.repository import Repository
from app.service import Service


@asynccontextmanager
async def get_session() -> typing.AsyncGenerator[AsyncSession, None]:
    session = Session()

    try:
        yield session
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


@asynccontextmanager
async def get_repository() -> typing.AsyncGenerator[Repository, None]:
    async with get_session() as session:
        repository = Repository(session=session)

        yield repository


@asynccontextmanager
async def get_redis() -> typing.AsyncGenerator[AsyncRedis, None]:
    async with AsyncRedis(host=config.redis.host, port=config.redis.port) as redis:
        yield redis


@asynccontextmanager
async def get_service() -> typing.AsyncGenerator[Service, None]:
    async with get_repository() as repository, get_redis() as redis:
        service = Service(repository=repository, redis=redis)

        yield service
