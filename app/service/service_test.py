import uuid
from datetime import datetime
from unittest.mock import Mock, call

import pytest
import pytz
from pytest_mock import MockerFixture

from app import schema, tasks
from app.config import config
from app.repository import Repository
from app.util import RelativeDelta

from .service import Service


@pytest.fixture
def repository(mocker: MockerFixture) -> Repository | Mock:
    return mocker.create_autospec(spec=Repository)


@pytest.fixture
def service(repository: Repository | Mock) -> Service:
    return Service(repository=repository)


@pytest.fixture
def load_configuration_success_mocks(mocker: MockerFixture) -> None:
    mocker.patch.object(tasks.send_event_notification_message_task, "apply_async")


async def test_service_load_configuration_success(
    mocker: MockerFixture,
    repository: Repository | Mock,
    service: Service,
    load_configuration_success_mocks,
):
    now = datetime.now(tz=pytz.utc)

    timezone = pytz.timezone("Europe/Kyiv").zone or ""
    chat_id = 1234

    good_event = schema.EventInput(
        name="good name",
        initial_date=now + RelativeDelta(days=5),
        offset=schema.Period(days="1"),
    )

    bad_event = schema.EventInput(
        name="bad name",
        initial_date=now - RelativeDelta(days=5),
    )

    configuration = schema.ConfigurationInput(
        timezone=timezone,
        events=[
            good_event,
            bad_event,
        ],
    )

    configuration_raw = {
        "timezone": "Europe/Kyiv",
        "events": [
            {
                "name": "good event",
                "initial_date": "03-10-2024 16:00:00 +0200",
            },
        ],
    }

    event_id = uuid.uuid4()

    mocker.patch.object(uuid, "uuid4", return_value=event_id)
    spy_event_notification_message_task = mocker.spy(
        tasks.send_event_notification_message_task, "apply_async",
    )

    await service.load_configuration(
        chat_id=chat_id, configuration=configuration, configuration_raw=configuration_raw,
    )

    repository.delete_chat_events.assert_called_once_with(chat_id=chat_id)
    repository.upsert_chat.assert_called_once_with(
        chat=schema.Chat(
            id=chat_id,
            timezone=timezone,
            config=configuration_raw,
        ),
    )
    spy_event_notification_message_task.assert_has_calls(
        [
            call(
                kwargs={"event_id": str(event_id)},
                eta=good_event.initial_date - RelativeDelta(days=1),
            ),
        ],
    )
    repository.upsert_events.assert_called_once_with(
        events=[
            schema.Event(
                id=event_id,
                chat_id=chat_id,
                name=good_event.name,
                initial_date=good_event.initial_date,
                next_date=good_event.initial_date,
                offset=good_event.offset,
            ),
        ],
    )


def test_service_update_event_next_date(service: Service):
    now = datetime.now(tz=pytz.utc)
    event_id = uuid.uuid4()

    cases = [
        (
            schema.Event(
                id=event_id,
                chat_id=0,
                name="Test",
                initial_date=now,
                next_date=now + RelativeDelta(minutes=10),
                times_occurred=0,
            ),
            schema.Event(
                id=event_id,
                chat_id=0,
                name="Test",
                initial_date=now,
                next_date=now + RelativeDelta(minutes=10),
                times_occurred=0,
            ),
        ),
        (
            schema.Event(
                id=event_id,
                chat_id=0,
                name="Test",
                initial_date=now,
                next_date=now - RelativeDelta(minutes=10),
                times_occurred=0,
            ),
            None,
        ),
        (
            schema.Event(
                id=event_id,
                chat_id=0,
                name="Test",
                initial_date=now,
                next_date=now,
                times_occurred=0,
            ),
            None,
        ),
        (
            schema.Event(
                id=event_id,
                chat_id=0,
                name="Test",
                initial_date=now,
                next_date=now + RelativeDelta(minutes=2),
                times_occurred=0,
                offset=schema.Period(minutes="2"),
            ),
            None,
        ),
        (
            schema.Event(
                id=event_id,
                chat_id=0,
                name="Test",
                initial_date=now - RelativeDelta(minutes=10),
                next_date=now - RelativeDelta(minutes=10),
                times_occurred=0,
                periodicity=schema.Period(minutes="15"),
            ),
            schema.Event(
                id=event_id,
                chat_id=0,
                name="Test",
                initial_date=now - RelativeDelta(minutes=10),
                next_date=now + RelativeDelta(minutes=5),
                times_occurred=1,
                periodicity=schema.Period(minutes="15"),
            ),
        ),
        (
            schema.Event(
                id=event_id,
                chat_id=0,
                name="Test",
                initial_date=now - RelativeDelta(minutes=10),
                next_date=now - RelativeDelta(minutes=10),
                times_occurred=0,
                offset=schema.Period(minutes="4"),
                periodicity=schema.Period(minutes="15"),
            ),
            schema.Event(
                id=event_id,
                chat_id=0,
                name="Test",
                initial_date=now - RelativeDelta(minutes=10),
                next_date=now + RelativeDelta(minutes=20),
                times_occurred=2,
                offset=schema.Period(minutes="4"),
                periodicity=schema.Period(minutes="15"),
            ),
        ),
    ]

    for event, expected in cases:
        actual = service.update_event_next_date(event=event)
        assert expected == actual


def test_service_evaluate_event_periodicity(service: Service):
    now = datetime.now(tz=pytz.utc)

    cases = [
        (
            schema.Event(
                chat_id=0,
                name="",
                initial_date=now,
                next_date=now,
                periodicity=schema.Period(days="2 + 3 * (t % 2)"),
                times_occurred=0,
            ),
            RelativeDelta(days=2),
        ),
        (
            schema.Event(
                chat_id=0,
                name="",
                initial_date=now,
                next_date=now,
                periodicity=schema.Period(days="2 + 3 * (t % 2)", minutes="10"),
                times_occurred=1,
            ),
            RelativeDelta(days=5, minutes=10),
        ),
        (
            schema.Event(
                chat_id=0,
                name="",
                initial_date=now,
                next_date=now,
                periodicity=schema.Period(seconds="10"),
                times_occurred=1,
            ),
            config.min_periodicity,
        ),
        (
            schema.Event(
                chat_id=0,
                name="",
                initial_date=now,
                next_date=now,
                periodicity=None,
                times_occurred=1,
            ),
            config.min_periodicity,
        ),
    ]

    for event, expected in cases:
        actual = service.evaluate_event_periodicity(event=event)
        assert expected == actual


def test_service_evaluate_event_offset(service: Service):
    now = datetime.now(tz=pytz.utc)

    cases = [
        (
            schema.Event(
                chat_id=0,
                name="",
                initial_date=now,
                next_date=now,
                offset=schema.Period(days="2 + 3 * (t % 2)"),
                times_occurred=0,
            ),
            RelativeDelta(days=2),
        ),
        (
            schema.Event(
                chat_id=0,
                name="",
                initial_date=now,
                next_date=now,
                offset=schema.Period(days="2 + 3 * (t % 2)", minutes="10"),
                times_occurred=1,
            ),
            RelativeDelta(days=5, minutes=10),
        ),
        (
            schema.Event(
                chat_id=0,
                name="",
                initial_date=now,
                next_date=now,
                offset=None,
                times_occurred=1,
            ),
            RelativeDelta(),
        ),
    ]

    for event, expected in cases:
        actual = service.evaluate_event_offset(event=event)
        assert expected == actual


def test_service_evaluate_period(service: Service):
    cases = [
        (0, schema.Period(days="4"), RelativeDelta(days=4)),
        (6, schema.Period(days="t"), RelativeDelta(days=6)),
        (6, schema.Period(days="n"), RelativeDelta(days=7)),
        (0, schema.Period(days="2 + 3 * (n % 2)"), RelativeDelta(days=5)),
        (1, schema.Period(days="2 + 3 * (n % 2)"), RelativeDelta(days=2)),
        (0, schema.Period(years="t + 1", days="4"), RelativeDelta(years=1, days=4)),
        (1, schema.Period(days="n + t"), RelativeDelta(days=3)),
        (
            0,
            schema.Period(
                years="1", months="1", weeks="1", days="1", hours="1", minutes="1", seconds="1",
            ),
            RelativeDelta(years=1, months=1, weeks=1, days=1, hours=1, minutes=1, seconds=1),
        ),
    ]

    for times_occurred, period, expected in cases:
        actual = service.evaluate_period(period=period, t=times_occurred)
        assert expected == actual
