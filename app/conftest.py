import asyncio
import typing

import pytest
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from testcontainers.postgres import PostgresContainer

from app.models import Base


@pytest.fixture(scope="session")
def event_loop() -> typing.Generator[asyncio.AbstractEventLoop, None, None]:
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def setup_testcontainers(
    event_loop: asyncio.AbstractEventLoop,
) -> typing.Generator[None, None, None]:
    postgres = PostgresContainer("postgres:17-alpine")
    postgres.start()

    global engine, Session

    engine = create_async_engine(url=postgres.get_connection_url(driver="asyncpg"), echo=False)
    Session = async_sessionmaker(bind=engine, autoflush=False)

    try:
        yield
    finally:
        postgres.stop()


@pytest.fixture
async def db_connection(setup_testcontainers: None) -> typing.AsyncGenerator[AsyncConnection, None]:
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
