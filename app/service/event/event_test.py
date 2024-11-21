from unittest.mock import call

import pytest
from pytest_mock import MockerFixture

from app import schema
from app.repository import Repository
from app.service import Service


async def test_event_service_upsert_success(
    mocker: MockerFixture,
    service: Service,
    repository: Repository,
    event: schema.Event,
) -> None:
    mocker.patch.object(repository.event, "upsert", autospec=True)

    await service.event.upsert(event=event)

    repository.event.upsert.assert_awaited_once_with(event=event)


@pytest.fixture
def event_service_get_mocks(
    mocker: MockerFixture,
    repository: Repository,
    event: schema.Event,
) -> None:
    mocker.patch.object(repository.event, "get", return_value=event, autospec=True)
    mocker.patch.object(repository.event, "upsert", autospec=True)


async def test_event_service_get_by_id_success(
    event_service_get_mocks: None,
    service: Service,
    repository: Repository,
    event: schema.Event,
) -> None:
    filter_ = schema.EventGetFilter(id=event.id)

    result = await service.event.get(filter_=filter_)

    repository.event.get.assert_awaited_once_with(filter_=filter_)
    assert event == result


async def test_event_service_get_by_id_cache_create_success(
    event_service_get_mocks: None,
    service: Service,
    repository: Repository,
    event: schema.Event,
) -> None:
    filter_ = schema.EventGetFilter(id=event.id)

    result1 = await service.event.get(filter_=filter_)
    result2 = await service.event.get(filter_=filter_)

    repository.event.get.assert_awaited_once_with(filter_=filter_)
    assert event == result1 == result2


async def test_event_service_get_by_id_cache_delete_on_upsert_success(
    event_service_get_mocks: None,
    service: Service,
    repository: Repository,
    event: schema.Event,
) -> None:
    new_event = event.model_copy(update={"name": "New Event Name"}, deep=True)
    repository.event.get.side_effect = [event, new_event]

    filter_ = schema.EventGetFilter(id=event.id)

    result1 = await service.event.get(filter_=filter_)

    await service.event.upsert(event=new_event)

    result2 = await service.event.get(filter_=filter_)

    repository.event.get.assert_has_awaits(
        [
            call(filter_=filter_),
            call(filter_=filter_),
        ],
    )
    assert event == result1
    assert new_event == result2


async def test_event_service_delete_by_chat_id_success(
    mocker: MockerFixture,
    service: Service,
    repository: Repository,
) -> None:
    mocker.patch.object(repository.event, "delete", autospec=True)

    filter_ = schema.EventDeleteFilter(chat_id=1)

    await service.event.delete(filter_=filter_)

    repository.event.delete.assert_awaited_once_with(filter_=filter_)
