import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import models, schema
from app.repository import Repository


async def test_event_repository_upsert_insert_success(
    db_session: AsyncSession,
    repository: Repository,
    chat: schema.Chat,
    event: schema.Event,
) -> None:
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
    chat: schema.Chat,
    event: schema.Event,
) -> None:
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


async def test_event_repository_get_success(
    repository: Repository,
    chat: schema.Chat,
    event: schema.Event,
) -> None:
    await repository.chat.upsert(chat=chat)
    await repository.event.upsert(event=event)

    new_event = await repository.event.get(filter_=schema.EventGetFilter(id=event.id))

    assert event == new_event


async def test_event_repository_delete_by_chat_id_success(
    db_session: AsyncSession,
    repository: Repository,
    chat: schema.Chat,
    event: schema.Event,
) -> None:
    await repository.chat.upsert(chat=chat)
    await repository.event.upsert(event=event)
    await repository.event.upsert(event=event.model_copy(update={"id": uuid.uuid4()}, deep=True))

    assert (
        len(
            (await db_session.execute(select(models.Event).where(models.Event.chat_id == chat.id)))
            .scalars()
            .all(),
        )
        == 2
    )

    await repository.event.delete(filter_=schema.EventDeleteFilter(chat_id=chat.id))

    assert (
        len(
            (await db_session.execute(select(models.Event).where(models.Event.chat_id == chat.id)))
            .scalars()
            .all(),
        )
        == 0
    )
