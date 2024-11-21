import asyncio
import typing
from datetime import datetime

import pytest
import pytz
from redis.asyncio import Redis as AsyncRedis
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import AsyncRedisContainer

from app import schema
from app.models import Base
from app.util.util import RelativeDelta


@pytest.fixture(scope="session")
def event_loop() -> typing.Generator[asyncio.AbstractEventLoop, None, None]:
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def postgres_container() -> typing.Generator[PostgresContainer, None, None]:
    with PostgresContainer(image="postgres:17-alpine") as postgres:
        global engine, Session

        engine = create_async_engine(url=postgres.get_connection_url(driver="asyncpg"), echo=False)
        Session = async_sessionmaker(bind=engine, autoflush=False)

        yield postgres


@pytest.fixture(scope="session")
def redis_container() -> typing.Generator[AsyncRedisContainer, None, None]:
    with AsyncRedisContainer(image="redis:7.4-alpine") as redis:
        yield redis


@pytest.fixture(scope="session")
def setup_test_environment(
    event_loop: asyncio.AbstractEventLoop,
    postgres_container: PostgresContainer,
    redis_container: AsyncRedisContainer,
) -> None:
    return


@pytest.fixture
async def db_connection(
    setup_test_environment: None,
) -> typing.AsyncGenerator[AsyncConnection, None]:
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

        yield connection


@pytest.fixture
async def db_session(db_connection: AsyncConnection) -> typing.AsyncGenerator[AsyncSession, None]:
    async with db_connection.begin_nested() as transaction:
        session = Session(bind=db_connection, join_transaction_mode="create_savepoint")

        try:
            yield session
        finally:
            await session.close()
            await transaction.rollback()


@pytest.fixture
async def redis(
    redis_container: AsyncRedisContainer,
) -> typing.AsyncGenerator[AsyncRedis, None]:
    redis = await redis_container.get_async_client()

    try:
        yield redis
    finally:
        async for key in redis.scan_iter():
            await redis.delete(key)

        await redis.close()


@pytest.fixture
def chat() -> schema.Chat:
    return schema.Chat(
        id=1,
        timezone="Etc/UTC",
        config={"timezone": "Etc/UTC", "events": []},
    )


@pytest.fixture
def event(chat: schema.Chat) -> schema.Event:
    now = datetime.now(tz=pytz.utc)

    return schema.Event(
        chat_id=chat.id,
        name="Event name",
        description="Event description",
        initial_date=now,
        next_date=now + RelativeDelta(weeks=1),
        periodicity=schema.Period(
            weeks="1",
        ),
        offset=schema.Period(
            weeks="1",
            minutes="10",
        ),
        times_occurred=1,
    )


@pytest.fixture
def occurrence(event: schema.Event) -> schema.Occurrence:
    now = datetime.now(tz=pytz.utc)

    return schema.Occurrence(
        event_id=event.id,
        message_id=1,
        created_at=now,
    )
