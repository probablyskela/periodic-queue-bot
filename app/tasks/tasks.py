import asyncio
import logging
import uuid

import aiogram
import pytz
from celery import Celery

from app import schema
from app.config import config
from app.dependencies import get_service
from app.keyboards import build_occurrence_keyboard

logger = logging.getLogger(__name__)

celery = Celery(broker=config.rabbitmq_url)


@celery.task
def send_event_notification_message_task(event_id: str) -> None:
    async def task() -> None:
        try:
            event_uuid = uuid.UUID(event_id, version=4)
        except ValueError:
            logger.exception(f"can't send notification message: invalid event id: {event_id}.")
            return

        async with get_service() as service:
            event = await service.get_event(event_id=event_uuid)
            if event is None:
                logger.warning(
                    f"can't send notification message: event with id: {event_id} not found.",
                )
                return

            chat = await service.get_chat(chat_id=event.chat_id)
            if chat is None:
                logger.warning(
                    f"can't send notification message: chat with id: {event.chat_id} not found.",
                )
                return

            occurrence = schema.Occurrence(
                event_id=event.id,
                message_id=-1,
                created_at=event.next_date,
            )

            date = event.next_date.astimezone(tz=pytz.timezone(zone=chat.timezone))

            async with aiogram.Bot(token=config.token) as bot:
                message = await bot.send_message(
                    chat_id=event.chat_id,
                    text=(
                        f"Event {event.name} starts on {date.strftime("%b %d %Y at %H:%M")}!\n"
                        f"{event.description}\n"
                    ),
                    reply_markup=build_occurrence_keyboard(occurrence_id=occurrence.id),
                )

            occurrence.message_id = message.message_id
            await service.insert_occurrence(occurrence=occurrence)

            event = service.update_event_next_date(event=event)
            if event is None:
                return
            await service.upsert_event(event=event)

            send_event_notification_message_task.apply_async(
                kwargs={"event_id": str(event.id)},
                eta=event.next_date - service.evaluate_event_offset(event=event),
            )

    loop = asyncio.get_event_loop()
    loop.run_until_complete(task())
