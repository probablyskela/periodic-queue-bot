import uuid
from datetime import datetime

import pytz
from pytest_mock import MockerFixture

from app import schema
from app.repository import Repository
from app.service import Service
from app.util.util import RelativeDelta


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


async def test_occurrence_service_generate_notification_message_text_success(
    service: Service,
) -> None:
    now = datetime(year=2024, month=11, day=18, hour=9, minute=40, second=0, tzinfo=pytz.utc)
    cases = [
        (
            schema.Event(
                chat_id=1,
                name="Event Name",
                initial_date=now,
                next_date=now,
            ),
            schema.Chat(
                id=1,
                timezone="Etc/UTC",
                config={},
            ),
            None,
            "Event Name starts on Monday, Nov 18 at 09:40:00!\n",
        ),
        (
            schema.Event(
                chat_id=1,
                name="Event Name",
                initial_date=now,
                next_date=now + RelativeDelta(months=1),
            ),
            schema.Chat(
                id=1,
                timezone="Europe/Kyiv",
                config={},
            ),
            None,
            "Event Name starts on Wednesday, Dec 18 at 11:40:00!\n",
        ),
        (
            schema.Event(
                chat_id=1,
                name="Event Name",
                initial_date=now,
                next_date=now + RelativeDelta(months=12),
            ),
            schema.Chat(
                id=1,
                timezone="Europe/Kyiv",
                config={},
            ),
            None,
            "Event Name starts on Tuesday, Nov 18, 2025 at 11:40:00!\n",
        ),
        (
            schema.Event(
                chat_id=1,
                name="Event Name",
                description="Event Description",
                initial_date=now,
                next_date=now,
            ),
            schema.Chat(
                id=1,
                timezone="Europe/Kyiv",
                config={},
            ),
            None,
            "Event Name starts on Monday, Nov 18 at 11:40:00!\nEvent Description\n",
        ),
        (
            schema.Event(
                chat_id=1,
                name="Event Name",
                description="Event Description",
                initial_date=now,
                next_date=now,
            ),
            schema.Chat(
                id=1,
                timezone="Europe/Kyiv",
                config={},
            ),
            [
                schema.Entry(
                    occurrence_id=uuid.uuid4(),
                    full_name="Full Name1",
                    username="username1",
                    user_id=1,
                    created_at=now,
                    is_skipping=True,
                    is_done=False,
                ),
                schema.Entry(
                    occurrence_id=uuid.uuid4(),
                    full_name="Full Name2",
                    username=None,
                    user_id=1,
                    created_at=now,
                    is_skipping=False,
                    is_done=True,
                ),
                schema.Entry(
                    occurrence_id=uuid.uuid4(),
                    full_name="Full Name3",
                    username="username3",
                    user_id=1,
                    created_at=now,
                    is_skipping=False,
                    is_done=False,
                ),
                schema.Entry(
                    occurrence_id=uuid.uuid4(),
                    full_name="Full Name4",
                    username="username4",
                    user_id=1,
                    created_at=now,
                    is_skipping=False,
                    is_done=False,
                ),
            ],
            (
                "Event Name starts on Monday, Nov 18 at 11:40:00!\n"
                "Event Description\n"
                "Current queue:\n"
                "1. ⬇️ Full Name1 (@username1)\n"
                "2. 🆗 Full Name2\n"
                "3. Full Name3 (@username3) ⬅️\n"
                "4. Full Name4 (@username4)"
            ),
        ),
    ]

    for event, chat, entries, expected in cases:
        actual = service.occurrence.generate_notification_message_text(
            event=event,
            chat=chat,
            entries=entries,
        )
        assert expected == actual
