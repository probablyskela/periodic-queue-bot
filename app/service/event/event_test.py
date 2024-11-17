import uuid
from datetime import datetime

import pytz
from pytest_mock import MockerFixture

from app import schema
from app.repository import Repository
from app.service import Service
from app.util import RelativeDelta


async def test_event_service_upsert_success(
    mocker: MockerFixture,
    service: Service,
    repository: Repository,
) -> None:
    now = datetime.now(tz=pytz.utc)

    spy_repository_event_upsert = mocker.patch.object(repository.event, "upsert")

    event = schema.Event(
        chat_id=1,
        name="Some event",
        description="This event does occur",
        initial_date=now - RelativeDelta(days=1),
        next_date=now + RelativeDelta(days=1),
        periodicity=schema.Period(
            years="4",
            months="n + t",
            weeks="54",
            days="1",
            hours="t + 8 * n",
            minutes="3",
            seconds="10",
        ),
        offset=schema.Period(
            years="14",
            months="n * t",
            weeks="4",
            days="3",
            hours="3 * t - n",
            minutes="31",
            seconds="30",
        ),
        times_occurred=10,
    )

    await service.event.upsert(event=event)

    spy_repository_event_upsert.assert_awaited_once_with(event=event)


async def test_event_service_get_by_id_success(
    mocker: MockerFixture,
    service: Service,
    repository: Repository,
) -> None:
    spy_repository_event_get = mocker.patch.object(repository.event, "get")

    filter_ = schema.EventGetFilter(id=uuid.uuid4())

    event = await service.event.get(filter_=filter_)

    spy_repository_event_get.assert_awaited_once_with(filter_=filter_)
    assert event == spy_repository_event_get.return_value


async def test_event_service_delete_by_chat_id_success(
    mocker: MockerFixture,
    service: Service,
    repository: Repository,
) -> None:
    spy_repository_event_delete = mocker.patch.object(repository.event, "delete")

    filter_ = schema.EventDeleteFilter(chat_id=1)

    await service.event.delete(filter_=filter_)

    spy_repository_event_delete.assert_awaited_once_with(filter_=filter_)
