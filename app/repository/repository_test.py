import json
import uuid
from datetime import datetime

import pytest
import pytz
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app import models, schema
from app.util import RelativeDelta

from .repository import Repository


@pytest.fixture
async def repository(db_session: AsyncSession) -> Repository:
    return Repository(session=db_session)


async def test_database(db_session: AsyncSession):
    await db_session.execute(select(text("1")))


async def test_repository_upsert_chat_insert_success(
    db_session: AsyncSession, repository: Repository,
):
    chat_id = 1
    timezone = "Europe/Kyiv"
    configuration = {"timezone": "Europe/Kyiv", "events": []}

    chat = schema.Chat(
        id=chat_id,
        timezone=timezone,
        config=configuration,
    )

    await repository.upsert_chat(chat=chat)

    assert (
        await db_session.execute(
            select(models.Chat).where(
                models.Chat.id == chat.id,
                models.Chat.timezone == chat.timezone,
                # models.Chat.config == chat.config,  # I don't feel like testing this. Feel free to create a PR.
            ),
        )
    ).scalar_one_or_none() is not None


async def test_repository_upsert_chat_update_success(
    db_session: AsyncSession, repository: Repository,
):
    chat_id = 1
    timezone = "Europe/Kyiv"
    configuration = {"timezone": "Europe/Kyiv", "events": []}

    chat = schema.Chat(
        id=chat_id,
        timezone=timezone,
        config=configuration,
    )

    await repository.upsert_chat(chat=chat)

    assert (
        await db_session.execute(
            select(models.Chat).where(
                models.Chat.id == chat.id,
                models.Chat.timezone == chat.timezone,
            ),
        )
    ).scalar_one_or_none() is not None

    chat.timezone = "Etc/UTC"

    await repository.upsert_chat(chat=chat)

    assert (
        await db_session.execute(
            select(models.Chat).where(
                models.Chat.id == chat.id,
                models.Chat.timezone == chat.timezone,
            ),
        )
    ).scalar_one_or_none() is not None


async def test_repository_get_chat_by_id_success(repository: Repository):
    chat = schema.Chat(
        id=1,
        timezone="Europe/Kyiv",
        config={"timezone": "Europe/Kyiv", "events": []},
    )

    await repository.upsert_chat(chat=chat)

    new_chat = await repository.get_chat(chat_id=chat.id)

    assert chat == new_chat


async def test_repository_upsert_events_insert_success(
    db_session: AsyncSession, repository: Repository,
):
    chat_id = 1
    now = datetime.now(tz=pytz.utc)

    chat = schema.Chat(id=chat_id, timezone="Europe/Kyiv", config=json.loads("{}"))

    event = schema.Event(
        chat_id=chat_id,
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

    await repository.upsert_chat(chat=chat)
    await repository.upsert_events(events=[event])

    assert (
        await db_session.execute(
            select(models.Event).where(
                models.Event.id == event.id,
                models.Event.chat_id == event.chat_id,
                models.Event.name == event.name,
                models.Event.description == event.description,
                models.Event.initial_date == event.initial_date.replace(tzinfo=None),
                models.Event.next_date == event.next_date.replace(tzinfo=None),
                models.Event.periodicity_years
                == (event.periodicity.years if event.periodicity else None),
                models.Event.periodicity_months
                == (event.periodicity.months if event.periodicity else None),
                models.Event.periodicity_weeks
                == (event.periodicity.weeks if event.periodicity else None),
                models.Event.periodicity_days
                == (event.periodicity.days if event.periodicity else None),
                models.Event.periodicity_hours
                == (event.periodicity.hours if event.periodicity else None),
                models.Event.periodicity_minutes
                == (event.periodicity.minutes if event.periodicity else None),
                models.Event.periodicity_seconds
                == (event.periodicity.seconds if event.periodicity else None),
                models.Event.offset_years == (event.offset.years if event.offset else None),
                models.Event.offset_months == (event.offset.months if event.offset else None),
                models.Event.offset_weeks == (event.offset.weeks if event.offset else None),
                models.Event.offset_days == (event.offset.days if event.offset else None),
                models.Event.offset_hours == (event.offset.hours if event.offset else None),
                models.Event.offset_minutes == (event.offset.minutes if event.offset else None),
                models.Event.offset_seconds == (event.offset.seconds if event.offset else None),
                models.Event.times_occurred == event.times_occurred,
            ),
        )
    ).scalar_one_or_none() is not None


async def test_repository_upsert_events_update_success(
    db_session: AsyncSession, repository: Repository,
):
    chat_id = 1
    now = datetime.now(tz=pytz.utc)

    chat = schema.Chat(id=chat_id, timezone="Europe/Kyiv", config=json.loads("{}"))

    event = schema.Event(
        chat_id=chat_id,
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

    await repository.upsert_chat(chat=chat)
    await repository.upsert_events(events=[event])

    assert (
        await db_session.execute(
            select(models.Event).where(
                models.Event.id == event.id,
                models.Event.chat_id == event.chat_id,
                models.Event.name == event.name,
                models.Event.description == event.description,
                models.Event.initial_date == event.initial_date.replace(tzinfo=None),
                models.Event.next_date == event.next_date.replace(tzinfo=None),
                models.Event.periodicity_years
                == (event.periodicity.years if event.periodicity else None),
                models.Event.periodicity_months
                == (event.periodicity.months if event.periodicity else None),
                models.Event.periodicity_weeks
                == (event.periodicity.weeks if event.periodicity else None),
                models.Event.periodicity_days
                == (event.periodicity.days if event.periodicity else None),
                models.Event.periodicity_hours
                == (event.periodicity.hours if event.periodicity else None),
                models.Event.periodicity_minutes
                == (event.periodicity.minutes if event.periodicity else None),
                models.Event.periodicity_seconds
                == (event.periodicity.seconds if event.periodicity else None),
                models.Event.offset_years == (event.offset.years if event.offset else None),
                models.Event.offset_months == (event.offset.months if event.offset else None),
                models.Event.offset_weeks == (event.offset.weeks if event.offset else None),
                models.Event.offset_days == (event.offset.days if event.offset else None),
                models.Event.offset_hours == (event.offset.hours if event.offset else None),
                models.Event.offset_minutes == (event.offset.minutes if event.offset else None),
                models.Event.offset_seconds == (event.offset.seconds if event.offset else None),
                models.Event.times_occurred == event.times_occurred,
            ),
        )
    ).scalar_one_or_none() is not None

    new_event = schema.Event(
        chat_id=chat_id,
        name="Some other event",
        initial_date=now - RelativeDelta(days=1),
        next_date=now + RelativeDelta(days=1),
    )

    event.description = "Some new description"

    await repository.upsert_events(events=[new_event, event])

    assert len((await db_session.execute(select(models.Event))).scalars().all()) == 2

    assert (
        await db_session.execute(
            select(models.Event).where(
                models.Event.id == event.id,
                models.Event.chat_id == event.chat_id,
                models.Event.name == event.name,
                models.Event.description == event.description,
                models.Event.initial_date == event.initial_date.replace(tzinfo=None),
                models.Event.next_date == event.next_date.replace(tzinfo=None),
                models.Event.periodicity_years
                == (event.periodicity.years if event.periodicity else None),
                models.Event.periodicity_months
                == (event.periodicity.months if event.periodicity else None),
                models.Event.periodicity_weeks
                == (event.periodicity.weeks if event.periodicity else None),
                models.Event.periodicity_days
                == (event.periodicity.days if event.periodicity else None),
                models.Event.periodicity_hours
                == (event.periodicity.hours if event.periodicity else None),
                models.Event.periodicity_minutes
                == (event.periodicity.minutes if event.periodicity else None),
                models.Event.periodicity_seconds
                == (event.periodicity.seconds if event.periodicity else None),
                models.Event.offset_years == (event.offset.years if event.offset else None),
                models.Event.offset_months == (event.offset.months if event.offset else None),
                models.Event.offset_weeks == (event.offset.weeks if event.offset else None),
                models.Event.offset_days == (event.offset.days if event.offset else None),
                models.Event.offset_hours == (event.offset.hours if event.offset else None),
                models.Event.offset_minutes == (event.offset.minutes if event.offset else None),
                models.Event.offset_seconds == (event.offset.seconds if event.offset else None),
                models.Event.times_occurred == event.times_occurred,
            ),
        )
    ).scalar_one_or_none() is not None


async def test_repository_get_event_success(repository: Repository):
    chat_id = 1
    now = datetime.now(tz=pytz.utc)

    chat = schema.Chat(id=chat_id, timezone="Europe/Kyiv", config=json.loads("{}"))

    event = schema.Event(
        chat_id=chat_id,
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

    await repository.upsert_chat(chat=chat)
    await repository.upsert_events(events=[event])

    new_event = await repository.get_event(event_id=event.id)

    assert event == new_event


async def test_repository_delete_chat_events_success(
    db_session: AsyncSession, repository: Repository,
):
    chat_id = 1
    now = datetime.now(tz=pytz.utc)

    chat = schema.Chat(id=chat_id, timezone="Europe/Kyiv", config=json.loads("{}"))

    await repository.upsert_chat(chat=chat)
    await repository.upsert_events(
        events=[
            schema.Event(
                chat_id=chat_id,
                name="Some event",
                initial_date=now - RelativeDelta(days=1),
                next_date=now + RelativeDelta(days=1),
            ),
            schema.Event(
                chat_id=chat_id,
                name="Some other event",
                initial_date=now - RelativeDelta(days=3),
                next_date=now + RelativeDelta(days=5),
            ),
        ],
    )

    assert (
        len(
            (await db_session.execute(select(models.Event).where(models.Event.chat_id == chat_id)))
            .scalars()
            .all(),
        )
        == 2
    )

    await repository.delete_chat_events(chat_id=chat_id)

    assert (
        len(
            (await db_session.execute(select(models.Event).where(models.Event.chat_id == chat_id)))
            .scalars()
            .all(),
        )
        == 0
    )


async def test_repository_insert_occurrence_success(
    db_session: AsyncSession, repository: Repository,
):
    now = datetime.now(tz=pytz.utc)

    chat = schema.Chat(id=1, timezone="Europe/Kyiv", config={})
    event = schema.Event(chat_id=chat.id, name="Event name", initial_date=now, next_date=now)
    occurrence = schema.Occurrence(event_id=event.id, message_id=5, created_at=now)

    await repository.upsert_chat(chat=chat)
    await repository.upsert_events(events=[event])

    await repository.insert_occurrence(occurrence=occurrence)

    assert (
        await db_session.execute(
            select(models.Occurrence).where(
                models.Occurrence.id == occurrence.id,
                models.Occurrence.event_id == occurrence.event_id,
                models.Occurrence.message_id == occurrence.message_id,
                models.Occurrence.created_at == occurrence.created_at.replace(tzinfo=None),
            ),
        )
    ).scalar_one_or_none() is not None


async def test_repository_get_occurrence_success(repository: Repository):
    now = datetime.now(tz=pytz.utc)

    chat = schema.Chat(id=1, timezone="Europe/Kyiv", config={})
    event = schema.Event(chat_id=chat.id, name="Event name", initial_date=now, next_date=now)
    occurrence = schema.Occurrence(event_id=event.id, message_id=5, created_at=now)

    await repository.upsert_chat(chat=chat)
    await repository.upsert_events(events=[event])

    await repository.insert_occurrence(occurrence=occurrence)

    new_occurrence = await repository.get_occurrence(occurrence_id=occurrence.id)

    assert new_occurrence == occurrence


async def test_repository_upsert_entry_insert_success(
    db_session: AsyncSession, repository: Repository,
):
    now = datetime.now(tz=pytz.utc)

    chat = schema.Chat(id=1, timezone="Europe/Kyiv", config={})
    event = schema.Event(chat_id=chat.id, name="Event name", initial_date=now, next_date=now)
    occurrence = schema.Occurrence(event_id=event.id, message_id=5, created_at=now)
    entry = schema.Entry(
        occurrence_id=occurrence.id,
        username=None,
        full_name="Me",
        user_id=5,
        created_at=now,
        is_skipping=False,
        is_done=True,
    )

    await repository.upsert_chat(chat=chat)
    await repository.upsert_events(events=[event])
    await repository.insert_occurrence(occurrence=occurrence)

    await repository.upsert_entry(entry=entry)

    assert (
        await db_session.execute(
            select(models.Entry).where(
                models.Entry.id == entry.id,
                models.Entry.occurrence_id == entry.occurrence_id,
                models.Entry.full_name == entry.full_name,
                models.Entry.username == entry.username,
                models.Entry.user_id == entry.user_id,
                models.Entry.created_at == entry.created_at.replace(tzinfo=None),
                models.Entry.is_skipping == entry.is_skipping,
                models.Entry.is_done == entry.is_done,
            ),
        )
    ).scalar_one_or_none() is not None


async def test_repository_upsert_entry_update_success(
    db_session: AsyncSession, repository: Repository,
):
    now = datetime.now(tz=pytz.utc)

    chat = schema.Chat(id=1, timezone="Europe/Kyiv", config={})
    event = schema.Event(chat_id=chat.id, name="Event name", initial_date=now, next_date=now)
    occurrence = schema.Occurrence(event_id=event.id, message_id=5, created_at=now)
    entry = schema.Entry(
        occurrence_id=occurrence.id,
        username=None,
        full_name="Me",
        user_id=5,
        created_at=now,
        is_skipping=False,
        is_done=True,
    )

    await repository.upsert_chat(chat=chat)
    await repository.upsert_events(events=[event])
    await repository.insert_occurrence(occurrence=occurrence)

    await repository.upsert_entry(entry=entry)

    assert (
        await db_session.execute(
            select(models.Entry).where(
                models.Entry.id == entry.id,
                models.Entry.occurrence_id == entry.occurrence_id,
                models.Entry.full_name == entry.full_name,
                models.Entry.username == entry.username,
                models.Entry.user_id == entry.user_id,
                models.Entry.created_at == entry.created_at.replace(tzinfo=None),
                models.Entry.is_skipping == entry.is_skipping,
                models.Entry.is_done == entry.is_done,
            ),
        )
    ).scalar_one_or_none() is not None

    entry.is_skipping = True
    await repository.upsert_entry(entry=entry)

    assert len((await db_session.execute(select(models.Entry))).scalars().all()) == 1

    assert (
        await db_session.execute(
            select(models.Entry).where(
                models.Entry.id == entry.id,
                models.Entry.occurrence_id == entry.occurrence_id,
                models.Entry.full_name == entry.full_name,
                models.Entry.username == entry.username,
                models.Entry.user_id == entry.user_id,
                models.Entry.created_at == entry.created_at.replace(tzinfo=None),
                models.Entry.is_skipping == entry.is_skipping,
                models.Entry.is_done == entry.is_done,
            ),
        )
    ).scalar_one_or_none() is not None


async def test_repository_get_entries_success(repository: Repository):
    now = datetime.now(tz=pytz.utc)

    chat = schema.Chat(id=1, timezone="Europe/Kyiv", config={})
    event = schema.Event(chat_id=chat.id, name="Event name", initial_date=now, next_date=now)
    occurrence = schema.Occurrence(event_id=event.id, message_id=5, created_at=now)

    old_entry = schema.Entry(
        occurrence_id=occurrence.id,
        username=None,
        full_name="Me",
        user_id=5,
        created_at=now - RelativeDelta(days=10),
        is_skipping=False,
        is_done=False,
    )
    new_entry = schema.Entry(
        occurrence_id=occurrence.id,
        username=None,
        full_name="Me",
        user_id=5,
        created_at=now,
        is_skipping=False,
        is_done=False,
    )

    await repository.upsert_chat(chat=chat)
    await repository.upsert_events(events=[event])
    await repository.insert_occurrence(occurrence=occurrence)

    await repository.upsert_entry(entry=new_entry)
    await repository.upsert_entry(entry=old_entry)

    entries = await repository.get_entries(occurrence_id=occurrence.id)

    assert entries == [old_entry, new_entry]


async def test_repository_get_entry_success(repository: Repository):
    now = datetime.now(tz=pytz.utc)
    user_id = 5

    chat = schema.Chat(id=1, timezone="Europe/Kyiv", config={})
    event = schema.Event(chat_id=chat.id, name="Event name", initial_date=now, next_date=now)
    occurrence = schema.Occurrence(event_id=event.id, message_id=5, created_at=now)

    entry = schema.Entry(
        occurrence_id=occurrence.id,
        username=None,
        full_name="Me",
        user_id=user_id,
        created_at=now - RelativeDelta(days=10),
        is_skipping=False,
        is_done=False,
    )

    await repository.upsert_chat(chat=chat)
    await repository.upsert_events(events=[event])
    await repository.insert_occurrence(occurrence=occurrence)

    await repository.upsert_entry(entry=entry)

    new_entry = await repository.get_entry(occurrence_id=occurrence.id, user_id=user_id)

    assert new_entry == entry


async def test_repository_get_entry_success_none(repository: Repository):
    assert (await repository.get_entry(occurrence_id=uuid.uuid4(), user_id=1)) is None


async def test_repository_delete_last_user_entry_success(
    db_session: AsyncSession, repository: Repository,
):
    now = datetime.now(tz=pytz.utc)
    user_id = 5

    chat = schema.Chat(id=1, timezone="Europe/Kyiv", config={})
    event = schema.Event(chat_id=chat.id, name="Event name", initial_date=now, next_date=now)
    occurrence = schema.Occurrence(event_id=event.id, message_id=5, created_at=now)

    old_entry = schema.Entry(
        occurrence_id=occurrence.id,
        username=None,
        full_name="Me",
        user_id=user_id,
        created_at=now - RelativeDelta(days=10),
        is_skipping=False,
        is_done=False,
    )
    new_entry = schema.Entry(
        occurrence_id=occurrence.id,
        username=None,
        full_name="Me",
        user_id=user_id,
        created_at=now,
        is_skipping=False,
        is_done=False,
    )

    await repository.upsert_chat(chat=chat)
    await repository.upsert_events(events=[event])
    await repository.insert_occurrence(occurrence=occurrence)

    await repository.upsert_entry(entry=new_entry)
    await repository.upsert_entry(entry=old_entry)

    assert len((await db_session.execute(select(models.Entry))).scalars().all()) == 2

    await repository.delete_last_user_entry(occurence_id=occurrence.id, user_id=user_id)

    entries = (await db_session.execute(select(models.Entry))).scalars().all()

    assert len(entries) == 1
    assert entries[0].id == old_entry.id


async def test_repository_delete_last_user_entry_no_error_on_missing(repository: Repository):
    await repository.delete_last_user_entry(occurence_id=uuid.uuid4(), user_id=3)
