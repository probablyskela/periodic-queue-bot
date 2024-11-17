import uuid
from datetime import datetime

import pytz
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import models, schema
from app.repository import Repository
from app.util import RelativeDelta


async def test_entry_repository_upsert_insert_success(
    db_session: AsyncSession,
    repository: Repository,
) -> None:
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

    await repository.chat.upsert(chat=chat)
    await repository.event.upsert(event=event)
    await repository.occurrence.upsert(occurrence=occurrence)

    await repository.entry.upsert(entry=entry)

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


async def test_entry_repository_upsert_update_success(
    db_session: AsyncSession,
    repository: Repository,
) -> None:
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

    await repository.chat.upsert(chat=chat)
    await repository.event.upsert(event=event)
    await repository.occurrence.upsert(occurrence=occurrence)

    await repository.entry.upsert(entry=entry)

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
    await repository.entry.upsert(entry=entry)

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


async def test_entry_repository_get_many_success(repository: Repository) -> None:
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

    await repository.chat.upsert(chat=chat)
    await repository.event.upsert(event=event)
    await repository.occurrence.upsert(occurrence=occurrence)

    await repository.entry.upsert(entry=new_entry)
    await repository.entry.upsert(entry=old_entry)

    entries = await repository.entry.get_many(
        filter_=schema.EntryGetManyFilter(occurrence_id=occurrence.id),
    )

    assert entries == [old_entry, new_entry]


async def test_entry_repository_get_success(repository: Repository) -> None:
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

    await repository.chat.upsert(chat=chat)
    await repository.event.upsert(event=event)
    await repository.occurrence.upsert(occurrence=occurrence)

    await repository.entry.upsert(entry=entry)

    new_entry = await repository.entry.get(
        filter_=schema.EntryGetFilter(occurrence_id=occurrence.id, user_id=user_id),
    )

    assert new_entry == entry


async def test_entry_repository_get_success_none(repository: Repository) -> None:
    assert (
        await repository.entry.get(schema.EntryGetFilter(occurrence_id=uuid.uuid4(), user_id=1))
    ) is None


async def test_entry_repository_delete_success(
    db_session: AsyncSession,
    repository: Repository,
) -> None:
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

    await repository.chat.upsert(chat=chat)
    await repository.event.upsert(event=event)
    await repository.occurrence.upsert(occurrence=occurrence)

    await repository.entry.upsert(entry=entry)

    assert len((await db_session.execute(select(models.Entry))).scalars().all()) == 1

    await repository.entry.delete(
        filter_=schema.EntryDeleteFilter(occurrence_id=occurrence.id, user_id=user_id),
    )

    assert len((await db_session.execute(select(models.Entry))).scalars().all()) == 0
