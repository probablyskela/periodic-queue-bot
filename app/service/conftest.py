import pytest
from pytest_mock import MockerFixture
from sqlalchemy.ext.asyncio import AsyncSession

from app.repository import Repository
from app.service import Service


@pytest.fixture
def repository(mocker: MockerFixture) -> Repository:
    return Repository(session=mocker.create_autospec(spec=AsyncSession))


@pytest.fixture
def service(repository: Repository) -> Service:
    return Service(repository=repository)
