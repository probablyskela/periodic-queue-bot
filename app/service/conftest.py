import pytest
from pytest_mock import MockerFixture
from redis.asyncio import Redis as AsyncRedis
from sqlalchemy.ext.asyncio import AsyncSession

from app.repository import Repository
from app.service import Service


@pytest.fixture
def repository(mocker: MockerFixture) -> Repository:
    return Repository(session=mocker.create_autospec(spec=AsyncSession))


@pytest.fixture
def service(repository: Repository, redis: AsyncRedis) -> Service:
    return Service(repository=repository, redis=redis)
