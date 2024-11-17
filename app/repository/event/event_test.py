import json
from datetime import datetime

import pytz
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import models, schema
from app.repository import Repository
from app.util import RelativeDelta


async def test_event_repository_upsert_insert_success(
    db_session: AsyncSession,
    repository: Repository,
) -> None:
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

    await repository.chat.upsert(chat=chat)
    await repository.event.upsert(event=event)

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


async def test_event_repository_upsert_update_success(
    db_session: AsyncSession,
    repository: Repository,
) -> None:
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

    await repository.chat.upsert(chat=chat)
    await repository.event.upsert(event=event)

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

    event.description = "Some new description"

    await repository.event.upsert(event=event)

    assert len((await db_session.execute(select(models.Event))).scalars().all()) == 1

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


async def test_event_repository_get_success(repository: Repository) -> None:
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

    await repository.chat.upsert(chat=chat)
    await repository.event.upsert(event=event)

    new_event = await repository.event.get(filter_=schema.EventGetFilter(id=event.id))

    assert event == new_event


async def test_event_repository_delete_by_chat_id_success(
    db_session: AsyncSession,
    repository: Repository,
) -> None:
    chat_id = 1
    now = datetime.now(tz=pytz.utc)

    chat = schema.Chat(id=chat_id, timezone="Europe/Kyiv", config=json.loads("{}"))

    await repository.chat.upsert(chat=chat)
    await repository.event.upsert(
        event=schema.Event(
            chat_id=chat_id,
            name="Some event",
            initial_date=now - RelativeDelta(days=1),
            next_date=now + RelativeDelta(days=1),
        ),
    )

    assert (
        len(
            (await db_session.execute(select(models.Event).where(models.Event.chat_id == chat_id)))
            .scalars()
            .all(),
        )
        == 1
    )

    await repository.event.delete(filter_=schema.EventDeleteFilter(chat_id=chat_id))

    assert (
        len(
            (await db_session.execute(select(models.Event).where(models.Event.chat_id == chat_id)))
            .scalars()
            .all(),
        )
        == 0
    )
