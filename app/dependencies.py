import typing
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession

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
async def get_service() -> typing.AsyncGenerator[Service, None]:
    async with get_repository() as repository:
        service = Service(repository=repository)

        yield service
