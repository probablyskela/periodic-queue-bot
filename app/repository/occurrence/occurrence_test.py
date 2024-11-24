from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import models, schema
from app.repository import Repository


async def test_occurrence_repository_upsert_insert_success(
    db_session: AsyncSession,
    repository: Repository,
    chat: schema.Chat,
    event: schema.Event,
    occurrence: schema.Occurrence,
) -> None:
    await repository.chat.upsert(chat=chat)
    await repository.event.upsert(event=event)

    await repository.occurrence.upsert(occurrence=occurrence)

    assert (
        await db_session.execute(
            select(models.Occurrence).where(
                models.Occurrence.id == occurrence.id,
                models.Occurrence.event_id == occurrence.event.id,
                models.Occurrence.message_id == occurrence.message_id,
                models.Occurrence.created_at == occurrence.created_at.replace(tzinfo=None),
            ),
        )
    ).scalar_one_or_none() is not None


async def test_occurrence_repository_upsert_update_success(
    db_session: AsyncSession,
    repository: Repository,
    chat: schema.Chat,
    event: schema.Event,
    occurrence: schema.Occurrence,
) -> None:
    await repository.chat.upsert(chat=chat)
    await repository.event.upsert(event=event)

    await repository.occurrence.upsert(occurrence=occurrence)

    assert (
        await db_session.execute(
            select(models.Occurrence).where(
                models.Occurrence.id == occurrence.id,
                models.Occurrence.event_id == occurrence.event.id,
                models.Occurrence.message_id == occurrence.message_id,
                models.Occurrence.created_at == occurrence.created_at.replace(tzinfo=None),
            ),
        )
    ).scalar_one_or_none() is not None

    occurrence.message_id += 1

    await repository.occurrence.upsert(occurrence=occurrence)

    assert (
        await db_session.execute(
            select(models.Occurrence).where(
                models.Occurrence.id == occurrence.id,
                models.Occurrence.event_id == occurrence.event.id,
                models.Occurrence.message_id == occurrence.message_id,
                models.Occurrence.created_at == occurrence.created_at.replace(tzinfo=None),
            ),
        )
    ).scalar_one_or_none() is not None


async def test_occurrence_repository_get_success(
    repository: Repository,
    chat: schema.Chat,
    event: schema.Event,
    occurrence: schema.Occurrence,
) -> None:
    await repository.chat.upsert(chat=chat)
    await repository.event.upsert(event=event)

    await repository.occurrence.upsert(occurrence=occurrence)

    new_occurrence = await repository.occurrence.get(
        filter_=schema.OccurrenceGetFilter(id=occurrence.id),
    )

    assert new_occurrence == occurrence
