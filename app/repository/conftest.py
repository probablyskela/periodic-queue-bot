import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.repository import Repository


@pytest.fixture
async def repository(db_session: AsyncSession) -> Repository:
    return Repository(session=db_session)
