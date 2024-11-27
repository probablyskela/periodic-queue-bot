import contextlib
import logging
import uuid

import aiogram
import aiogram.exceptions

from app import schema
from app.config import config
from app.dependencies import get_service
from app.keyboards import build_occurrence_keyboard
from app.service import Service
from app.tasks.celery import celery

logger = logging.getLogger(__name__)


@celery.task(serializer="pickle")
async def send_notification_message_task(event_id: uuid.UUID) -> None:
    async with get_service() as service, aiogram.Bot(token=config.token) as bot:
        await send_notification_message(service=service, bot=bot, event_id=event_id)


@celery.task(serializer="pickle")
async def resend_notification_message_task(occurrence_id: uuid.UUID) -> None:
    async with get_service() as service, aiogram.Bot(token=config.token) as bot:
        await resend_notification_message(service=service, bot=bot, occurrence_id=occurrence_id)


async def send_notification_message(
    service: Service,
    bot: aiogram.Bot,
    event_id: uuid.UUID,
) -> None:
    event = await service.event.get(filter_=schema.EventGetFilter(id=event_id))
    if event is None:
        logger.warning(
            "can't send notification message: event with id: %s not found.",
            str(event_id),
        )
        return

    occurrence = schema.Occurrence(
        event=event,
        message_id=-1,
        created_at=event.next_date,
    )

    message = await bot.send_message(
        chat_id=event.chat.id,
        text=service.occurrence.generate_notification_message_text(occurrence=occurrence),
        reply_markup=build_occurrence_keyboard(occurrence_id=occurrence.id),
    )

    occurrence.message_id = message.message_id
    await service.occurrence.upsert(occurrence=occurrence)

    if service.evaluate_event_offset(event=event).s != 0:
        resend_notification_message_task.apply_async(
            kwargs={"occurrence_id": occurrence.id},
            eta=event.next_date,
        )

    event = service.update_event_next_date(event=event)
    if event is None:
        return
    await service.event.upsert(event=event)

    send_notification_message_task.apply_async(
        kwargs={"event_id": event.id},
        eta=event.next_date - service.evaluate_event_offset(event=event),
    )


async def resend_notification_message(
    service: Service,
    bot: aiogram.Bot,
    occurrence_id: uuid.UUID,
) -> None:
    occurrence = await service.occurrence.get(
        filter_=schema.OccurrenceGetFilter(id=occurrence_id),
    )
    if occurrence is None:
        logger.warning(
            "can't resend notification message: occurrence with id: %s not found.",
            str(occurrence_id),
        )
        return

    entries = await service.entry.get_many(
        filter_=schema.EntryGetManyFilter(occurrence_id=occurrence.id),
    )

    with contextlib.suppress(aiogram.exceptions.TelegramBadRequest):
        await bot.delete_message(
            chat_id=occurrence.event.chat.id,
            message_id=occurrence.message_id,
        )

    message = await bot.send_message(
        chat_id=occurrence.event.chat.id,
        text=service.occurrence.generate_notification_message_text(
            occurrence=occurrence,
            entries=entries,
        ),
        reply_markup=build_occurrence_keyboard(occurrence_id=occurrence.id),
    )

    occurrence.message_id = message.message_id
    await service.occurrence.upsert(occurrence=occurrence)
