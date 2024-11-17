import uuid
from datetime import datetime

import pytz
from pytest_mock import MockerFixture

from app import schema
from app.repository import Repository
from app.service import Service


async def test_occurrence_service_upsert_success(
    mocker: MockerFixture,
    service: Service,
    repository: Repository,
) -> None:
    spy_repository_occurrence_upsert = mocker.patch.object(repository.occurrence, "upsert")

    occurrence = schema.Occurrence(
        event_id=uuid.uuid4(),
        message_id=1,
        created_at=datetime.now(tz=pytz.utc),
    )

    await service.occurrence.upsert(occurrence=occurrence)

    spy_repository_occurrence_upsert.assert_awaited_once_with(occurrence=occurrence)


async def test_occurrence_service_get_by_id_success(
    mocker: MockerFixture,
    service: Service,
    repository: Repository,
) -> None:
    spy_repository_occurrence_get = mocker.patch.object(repository.occurrence, "get")

    filter_ = schema.OccurrenceGetFilter(id=uuid.uuid4())

    occurrence = await service.occurrence.get(filter_=filter_)

    spy_repository_occurrence_get.assert_awaited_once_with(filter_=filter_)
    assert occurrence == spy_repository_occurrence_get.return_value
