from datetime import datetime

import aiogram
import pytz

from app import callbacks, schema
from app.keyboards import build_occurrence_keyboard
from app.service import Service


async def occurrence_callback_handler(
    callback: aiogram.types.CallbackQuery,
    bot: aiogram.Bot,
    service: Service,
    callback_data: callbacks.OccurrenceCallbackFactory,
) -> None:
    now = datetime.now(tz=pytz.utc)

    occurrence = await service.occurrence.get(
        filter_=schema.OccurrenceGetFilter(id=callback_data.occurrence_id),
    )
    if occurrence is None:
        await callback.answer(text="Event is expired or invalid.")
        return

    entry = await service.entry.get(
        filter_=schema.EntryGetFilter(
            occurrence_id=occurrence.id,
            user_id=callback.from_user.id,
        ),
    )

    match callback_data.action:
        case callbacks.OccurrenceActionEnum.JOIN:
            if entry:
                if entry.is_done is True:
                    await callback.answer(text="You are already done. Can't join.")
                else:
                    await callback.answer(text="You are already in the queue.")
                return

            await service.entry.upsert(
                entry=schema.Entry(
                    occurrence_id=occurrence.id,
                    username=callback.from_user.username,
                    full_name=callback.from_user.full_name,
                    user_id=callback.from_user.id,
                    created_at=now,
                    is_skipping=False,
                    is_done=False,
                ),
            )
        case callbacks.OccurrenceActionEnum.LEAVE:
            if entry is None:
                await callback.answer(text="You are not in the queue.")
                return

            if entry.is_done is True:
                await callback.answer(text="You are already done. Can't leave.")
                return

            await service.entry.delete(
                filter_=schema.EntryDeleteFilter(
                    occurrence_id=occurrence.id,
                    user_id=callback.from_user.id,
                ),
            )

        case callbacks.OccurrenceActionEnum.SKIP:
            if entry is None:
                await callback.answer(text="You are not in the queue.")
                return

            if entry.is_done is True:
                await callback.answer(text="You are already done. Can't skip.")
                return

            entry.is_skipping = not entry.is_skipping
            await service.entry.upsert(entry=entry)

        case callbacks.OccurrenceActionEnum.DONE:
            if entry is None:
                await callback.answer(text="You are not in the queue.")
                return

            if entry.is_done is True:
                await callback.answer(text="You are already done.")
                return

            entry.is_skipping = False
            entry.is_done = True
            await service.entry.upsert(entry=entry)

    entries = await service.entry.get_many(
        filter_=schema.EntryGetManyFilter(occurrence_id=occurrence.id),
    )

    await bot.edit_message_text(
        text=service.occurrence.generate_notification_message_text(
            occurrence=occurrence,
            entries=entries,
        ),
        chat_id=occurrence.event.chat.id,
        message_id=occurrence.message_id,
        reply_markup=build_occurrence_keyboard(occurrence_id=occurrence.id),
    )

    await callback.answer(text="Success.")
