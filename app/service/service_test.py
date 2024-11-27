import uuid
from datetime import datetime
from unittest.mock import call

import pytest
import pytz
from pytest_mock import MockerFixture

from app import schema, tasks
from app.service import Service
from app.util import RelativeDelta


@pytest.fixture
def load_configuration_mocks(mocker: MockerFixture, service: Service) -> None:
    mocker.patch.object(tasks.send_notification_message_task, "apply_async", autospec=True)
    mocker.patch.object(service.event, "delete", autospec=True)
    mocker.patch.object(service.chat, "upsert", autospec=True)
    mocker.patch.object(service.event, "upsert", autospec=True)


async def test_service_load_configuration_success(
    load_configuration_mocks: None,
    mocker: MockerFixture,
    service: Service,
) -> None:
    now = datetime.now(tz=pytz.utc)

    chat_id = 1234
    timezone = pytz.timezone("Europe/Kyiv").zone or ""
    configuration_raw = {
        "timezone": "Europe/Kyiv",
        "events": [
            {
                "name": "good event",
                "initial_date": "03-10-2024 16:00:00 +0200",
            },
        ],
    }
    chat = schema.Chat(
        id=chat_id,
        timezone=timezone,
        config=configuration_raw,
    )

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

    event_id = uuid.uuid4()

    mocker.patch.object(uuid, "uuid4", return_value=event_id)

    await service.load_configuration(
        chat_id=chat_id,
        configuration=configuration,
        configuration_raw=configuration_raw,
    )

    service.event.delete.assert_called_once_with(
        filter_=schema.EventDeleteFilter(chat_id=chat_id),
    )
    service.chat.upsert.assert_called_once_with(chat=chat)
    tasks.send_notification_message_task.apply_async.assert_has_calls(
        [
            call(
                kwargs={"event_id": event_id},
                eta=good_event.initial_date - RelativeDelta(days=1),
            ),
        ],
    )
    service.event.upsert.assert_called_once_with(
        event=schema.Event(
            id=event_id,
            chat=chat,
            name=good_event.name,
            initial_date=good_event.initial_date,
            next_date=good_event.initial_date,
            offset=good_event.offset,
        ),
    )


def test_service_update_event_next_date(service: Service, chat: schema.Chat) -> None:
    now = datetime.now(tz=pytz.utc)
    event_id = uuid.uuid4()

    cases = [
        (
            schema.Event(
                id=event_id,
                chat=chat,
                name="Test",
                initial_date=now,
                next_date=now + RelativeDelta(minutes=10),
                times_occurred=0,
            ),
            schema.Event(
                id=event_id,
                chat=chat,
                name="Test",
                initial_date=now,
                next_date=now + RelativeDelta(minutes=10),
                times_occurred=0,
            ),
        ),
        (
            schema.Event(
                id=event_id,
                chat=chat,
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
                chat=chat,
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
                chat=chat,
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
                chat=chat,
                name="Test",
                initial_date=now - RelativeDelta(minutes=10),
                next_date=now - RelativeDelta(minutes=10),
                times_occurred=0,
                periodicity=schema.Period(minutes="15"),
            ),
            schema.Event(
                id=event_id,
                chat=chat,
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
                chat=chat,
                name="Test",
                initial_date=now - RelativeDelta(minutes=10),
                next_date=now - RelativeDelta(minutes=10),
                times_occurred=0,
                offset=schema.Period(minutes="4", seconds="30"),
                periodicity=schema.Period(minutes="15"),
            ),
            schema.Event(
                id=event_id,
                chat=chat,
                name="Test",
                initial_date=now - RelativeDelta(minutes=10),
                next_date=now + RelativeDelta(minutes=20),
                times_occurred=2,
                offset=schema.Period(minutes="4", seconds="30"),
                periodicity=schema.Period(minutes="15"),
            ),
        ),
    ]

    for event, expected in cases:
        actual = service.update_event_next_date(event=event)
        assert expected == actual


def test_service_evaluate_event_periodicity(service: Service, chat: schema.Chat) -> None:
    now = datetime.now(tz=pytz.utc)

    cases = [
        (
            schema.Event(
                chat=chat,
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
                chat=chat,
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
                chat=chat,
                name="",
                initial_date=now,
                next_date=now,
                periodicity=None,
                times_occurred=1,
            ),
            None,
        ),
        (
            schema.Event(
                chat=chat,
                name="",
                initial_date=now,
                next_date=now,
                periodicity=schema.Period(years="3"),
                times_occurred=1,
            ),
            None,
        ),
        (
            schema.Event(
                chat=chat,
                name="",
                initial_date=now,
                next_date=now,
                periodicity=schema.Period(seconds="10"),
                times_occurred=1,
            ),
            None,
        ),
    ]

    for event, expected in cases:
        actual = service.evaluate_event_periodicity(event=event)
        assert expected == actual


def test_service_evaluate_event_offset(service: Service, chat: schema.Chat) -> None:
    now = datetime.now(tz=pytz.utc)

    cases = [
        (
            schema.Event(
                chat=chat,
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
                chat=chat,
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
                chat=chat,
                name="",
                initial_date=now,
                next_date=now,
                offset=None,
                times_occurred=1,
            ),
            RelativeDelta(),
        ),
        (
            schema.Event(
                chat=chat,
                name="",
                initial_date=now,
                next_date=now,
                offset=schema.Period(minutes="-1"),
                times_occurred=1,
            ),
            RelativeDelta(),
        ),
        (
            schema.Event(
                chat=chat,
                name="",
                initial_date=now,
                next_date=now,
                offset=schema.Period(years="3"),
                times_occurred=1,
            ),
            RelativeDelta(),
        ),
    ]

    for event, expected in cases:
        actual = service.evaluate_event_offset(event=event)
        assert expected == actual


def test_service_evaluate_period(service: Service) -> None:
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
                years="1",
                months="1",
                weeks="1",
                days="1",
                hours="1",
                minutes="1",
                seconds="1",
            ),
            RelativeDelta(years=1, months=1, weeks=1, days=1, hours=1, minutes=1, seconds=1),
        ),
    ]

    for times_occurred, period, expected in cases:
        actual = service.evaluate_period(period=period, t=times_occurred)
        assert expected == actual
