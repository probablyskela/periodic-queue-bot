import uuid
from datetime import datetime

import pytz
from pytest_mock import MockerFixture

from app import schema
from app.repository import Repository
from app.service import Service


async def test_entry_service_upsert_success(
    mocker: MockerFixture,
    service: Service,
    repository: Repository,
) -> None:
    spy_repository_entry_upsert = mocker.patch.object(repository.entry, "upsert")

    entry = schema.Entry(
        occurrence_id=uuid.uuid4(),
        username=None,
        full_name="Full Name",
        user_id=1,
        created_at=datetime.now(tz=pytz.utc),
        is_skipping=False,
        is_done=True,
    )

    await service.entry.upsert(entry=entry)

    spy_repository_entry_upsert.assert_awaited_once_with(entry=entry)


async def test_entry_service_get_by_occurrence_id_and_user_id_success(
    mocker: MockerFixture,
    service: Service,
    repository: Repository,
) -> None:
    spy_repository_entry_get = mocker.patch.object(repository.entry, "get")

    filter_ = schema.EntryGetFilter(occurrence_id=uuid.uuid4(), user_id=1)

    entry = await service.entry.get(filter_=filter_)

    spy_repository_entry_get.assert_awaited_once_with(filter_=filter_)
    assert entry == spy_repository_entry_get.return_value


async def test_entry_service_get_many_by_occurrence_id_success(
    mocker: MockerFixture,
    service: Service,
    repository: Repository,
) -> None:
    spy_repository_entry_get_many = mocker.patch.object(repository.entry, "get_many")

    filter_ = schema.EntryGetManyFilter(occurrence_id=uuid.uuid4())

    entries = await service.entry.get_many(filter_=filter_)

    spy_repository_entry_get_many.assert_awaited_once_with(filter_=filter_)
    assert entries == spy_repository_entry_get_many.return_value


async def test_entry_service_delete_by_occurrence_id_and_user_id_success(
    mocker: MockerFixture,
    service: Service,
    repository: Repository,
) -> None:
    spy_repository_entry_delete = mocker.patch.object(repository.entry, "delete")

    filter_ = schema.EntryDeleteFilter(occurrence_id=uuid.uuid4(), user_id=1)

    await service.entry.delete(filter_=filter_)

    spy_repository_entry_delete.assert_awaited_once_with(filter_=filter_)
