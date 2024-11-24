import uuid
from datetime import datetime
from unittest.mock import call

import pytest
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
    occurrence: schema.Occurrence,
) -> None:
    mocker.patch.object(repository.occurrence, "upsert", autospec=True)

    await service.occurrence.upsert(occurrence=occurrence)

    repository.occurrence.upsert.assert_awaited_once_with(occurrence=occurrence)


@pytest.fixture
def occurrence_service_get_mocks(
    mocker: MockerFixture,
    repository: Repository,
    occurrence: schema.Occurrence,
) -> None:
    mocker.patch.object(repository.occurrence, "get", return_value=occurrence, autospec=True)
    mocker.patch.object(repository.occurrence, "upsert", autospec=True)


async def test_occurrence_service_get_by_id_success(
    occurrence_service_get_mocks: None,
    service: Service,
    repository: Repository,
    occurrence: schema.Occurrence,
) -> None:
    filter_ = schema.OccurrenceGetFilter(id=occurrence.id)

    result = await service.occurrence.get(filter_=filter_)

    repository.occurrence.get.assert_awaited_once_with(filter_=filter_)
    assert occurrence == result


async def test_occurrence_service_get_by_id_cache_create_success(
    occurrence_service_get_mocks: None,
    service: Service,
    repository: Repository,
    occurrence: schema.Occurrence,
) -> None:
    filter_ = schema.OccurrenceGetFilter(id=occurrence.id)

    result1 = await service.occurrence.get(filter_=filter_)
    result2 = await service.occurrence.get(filter_=filter_)

    repository.occurrence.get.assert_awaited_once_with(filter_=filter_)
    assert occurrence == result1 == result2


async def test_occurrence_service_get_by_id_cache_delete_on_upsert_success(
    occurrence_service_get_mocks: None,
    service: Service,
    repository: Repository,
    occurrence: schema.Occurrence,
) -> None:
    new_occurrence = occurrence.model_copy(update={"message_id": 100}, deep=True)
    repository.occurrence.get.side_effect = [occurrence, new_occurrence]

    filter_ = schema.OccurrenceGetFilter(id=occurrence.id)

    result1 = await service.occurrence.get(filter_=filter_)

    await service.occurrence.upsert(occurrence=new_occurrence)

    result2 = await service.occurrence.get(filter_=filter_)

    repository.occurrence.get.assert_has_awaits(
        [
            call(filter_=filter_),
            call(filter_=filter_),
        ],
    )
    assert occurrence == result1
    assert new_occurrence == result2


async def test_occurrence_service_generate_notification_message_text_success(
    service: Service,
    chat: schema.Chat,
    event: schema.Event,
) -> None:
    now = datetime(year=2024, month=11, day=18, hour=9, minute=40, second=0, tzinfo=pytz.utc)
    cases = [
        (
            schema.Occurrence(
                event=schema.Event(
                    chat=schema.Chat(
                        id=1,
                        timezone="Etc/UTC",
                        config={},
                    ),
                    name="Event Name",
                    initial_date=now,
                    next_date=now,
                ),
                message_id=1,
                created_at=now,
            ),
            None,
            "Event Name starts on Monday, Nov 18 at 09:40:00!\n",
        ),
        (
            schema.Occurrence(
                event=schema.Event(
                    chat=schema.Chat(
                        id=1,
                        timezone="Europe/Kyiv",
                        config={},
                    ),
                    name="Event Name",
                    initial_date=now,
                    next_date=now + RelativeDelta(months=1),
                ),
                message_id=1,
                created_at=now + RelativeDelta(months=1),
            ),
            None,
            "Event Name starts on Wednesday, Dec 18 at 11:40:00!\n",
        ),
        (
            schema.Occurrence(
                event=schema.Event(
                    chat=schema.Chat(
                        id=1,
                        timezone="Europe/Kyiv",
                        config={},
                    ),
                    name="Event Name",
                    initial_date=now,
                    next_date=now + RelativeDelta(months=12),
                ),
                message_id=1,
                created_at=now + RelativeDelta(months=12),
            ),
            None,
            "Event Name starts on Tuesday, Nov 18, 2025 at 11:40:00!\n",
        ),
        (
            schema.Occurrence(
                event=schema.Event(
                    chat=schema.Chat(
                        id=1,
                        timezone="Europe/Kyiv",
                        config={},
                    ),
                    name="Event Name",
                    description="Event Description",
                    initial_date=now,
                    next_date=now,
                ),
                message_id=1,
                created_at=now,
            ),
            None,
            "Event Name starts on Monday, Nov 18 at 11:40:00!\nEvent Description\n",
        ),
        (
            schema.Occurrence(
                event=schema.Event(
                    chat=schema.Chat(
                        id=1,
                        timezone="Europe/Kyiv",
                        config={},
                    ),
                    name="Event Name",
                    description="Event Description",
                    initial_date=now,
                    next_date=now,
                ),
                message_id=1,
                created_at=now,
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

    for occurrence, entries, expected in cases:
        actual = service.occurrence.generate_notification_message_text(
            occurrence=occurrence,
            entries=entries,
        )
        assert expected == actual
