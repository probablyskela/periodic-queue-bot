import uuid

from pytest_mock import MockerFixture

from app import schema
from app.repository import Repository
from app.service import Service


async def test_entry_service_upsert_success(
    mocker: MockerFixture,
    service: Service,
    repository: Repository,
    entry: schema.Entry,
) -> None:
    mocker.patch.object(repository.entry, "upsert", autospec=True)

    await service.entry.upsert(entry=entry)

    repository.entry.upsert.assert_awaited_once_with(entry=entry)


async def test_entry_service_get_by_occurrence_id_and_user_id_success(
    mocker: MockerFixture,
    service: Service,
    repository: Repository,
    entry: schema.Entry,
) -> None:
    mocker.patch.object(
        repository.entry,
        "get",
        return_value=entry.model_copy(deep=True),
        autospec=True,
    )

    filter_ = schema.EntryGetFilter(occurrence_id=uuid.uuid4(), user_id=1)

    result = await service.entry.get(filter_=filter_)

    repository.entry.get.assert_awaited_once_with(filter_=filter_)
    assert entry == result


async def test_entry_service_get_many_by_occurrence_id_success(
    mocker: MockerFixture,
    service: Service,
    repository: Repository,
    entry: schema.Entry,
) -> None:
    mocker.patch.object(
        repository.entry,
        "get_many",
        return_value=[entry.model_copy(deep=True)],
        autospec=True,
    )

    filter_ = schema.EntryGetManyFilter(occurrence_id=uuid.uuid4())

    result = await service.entry.get_many(filter_=filter_)

    repository.entry.get_many.assert_awaited_once_with(filter_=filter_)
    assert [entry] == result


async def test_entry_service_delete_by_occurrence_id_and_user_id_success(
    mocker: MockerFixture,
    service: Service,
    repository: Repository,
) -> None:
    mocker.patch.object(repository.entry, "delete", autospec=True)

    filter_ = schema.EntryDeleteFilter(occurrence_id=uuid.uuid4(), user_id=1)

    await service.entry.delete(filter_=filter_)

    repository.entry.delete.assert_awaited_once_with(filter_=filter_)
