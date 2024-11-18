import asyncio
import logging
import uuid

import aiogram
from celery import Celery

from app import schema
from app.config import config
from app.dependencies import get_service
from app.keyboards import build_occurrence_keyboard

logger = logging.getLogger(__name__)

celery = Celery(broker=config.rabbitmq_url)


async def send_notification_message(event_id: str) -> None:
    try:
        event_uuid = uuid.UUID(event_id, version=4)
    except ValueError:
        logger.exception(
            "can't send notification message: invalid event id: %s.",
            str(event_id),
        )
        return

    async with get_service() as service:
        event = await service.event.get(filter_=schema.EventGetFilter(id=event_uuid))
        if event is None:
            logger.warning(
                "can't send notification message: event with id: %s not found.",
                str(event_id),
            )
            return

        chat = await service.chat.get(filter_=schema.ChatGetFilter(id=event.chat_id))
        if chat is None:
            logger.warning(
                "can't send notification message: chat with id: %s not found.",
                str(event.chat_id),
            )
            return

        occurrence = schema.Occurrence(
            event_id=event.id,
            message_id=-1,
            created_at=event.next_date,
        )

        async with aiogram.Bot(token=config.token) as bot:
            message = await bot.send_message(
                chat_id=chat.id,
                text=service.occurrence.generate_notification_message_text(event=event, chat=chat),
                reply_markup=build_occurrence_keyboard(occurrence_id=occurrence.id),
            )

        occurrence.message_id = message.message_id
        await service.occurrence.upsert(occurrence=occurrence)

        if service.evaluate_event_offset(event=event).s != 0:
            resend_notification_message_task.apply_async(
                kwargs={"occurrence_id": str(occurrence.id)},
                eta=event.next_date,
            )

        event = service.update_event_next_date(event=event)
        if event is None:
            return
        await service.event.upsert(event=event)

        send_notification_message_task.apply_async(
            kwargs={"event_id": str(event.id)},
            eta=event.next_date - service.evaluate_event_offset(event=event),
        )


@celery.task
def send_notification_message_task(event_id: str) -> None:
    loop = asyncio.get_event_loop()
    loop.run_until_complete(send_notification_message(event_id=event_id))


async def resend_notification_message(occurrence_id: str) -> None:
    try:
        occurrence_uuid = uuid.UUID(occurrence_id, version=4)
    except ValueError:
        logger.exception(
            "can't resend notification message: invalid occurrence id: %s.",
            str(occurrence_id),
        )
        return

    async with get_service() as service:
        occurrence = await service.occurrence.get(
            filter_=schema.OccurrenceGetFilter(id=occurrence_uuid),
        )
        if occurrence is None:
            logger.warning(
                "can't resend notification message: occurrence with id: %s not found.",
                str(occurrence_uuid),
            )
            return

        event = await service.event.get(filter_=schema.EventGetFilter(id=occurrence.event_id))
        if event is None:
            logger.warning(
                "can't resend notification message: event with id: %s not found.",
                str(occurrence.event_id),
            )
            return

        chat = await service.chat.get(filter_=schema.ChatGetFilter(id=event.chat_id))
        if chat is None:
            logger.warning(
                "can't resend notification message: chat with id: %d not found.",
                str(event.chat_id),
            )
            return

        entries = await service.entry.get_many(
            filter_=schema.EntryGetManyFilter(occurrence_id=occurrence.id),
        )

        async with aiogram.Bot(token=config.token) as bot:
            await bot.delete_message(chat_id=chat.id, message_id=occurrence.message_id)

            message = await bot.send_message(
                chat_id=chat.id,
                text=service.occurrence.generate_notification_message_text(
                    event=event,
                    chat=chat,
                    entries=entries,
                ),
                reply_markup=build_occurrence_keyboard(occurrence_id=occurrence.id),
            )

        occurrence.message_id = message.message_id
        await service.occurrence.upsert(occurrence=occurrence)


@celery.task
def resend_notification_message_task(occurrence_id: str) -> None:
    loop = asyncio.get_event_loop()
    loop.run_until_complete(resend_notification_message(occurrence_id=occurrence_id))
