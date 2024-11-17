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

    occurrence = await service.get_occurrence(occurrence_id=callback_data.occurrence_id)
    if occurrence is None:
        await callback.answer(text="Event is expired or invalid.")
        return

    match callback_data.action:
        case callbacks.OccurrenceActionEnum.JOIN:
            entry = await service.get_entry(
                occurrence_id=occurrence.id,
                user_id=callback.from_user.id,
            )

            if entry:
                if entry.is_done is True:
                    await callback.answer(text="You are already done. Can't join.")
                else:
                    await callback.answer(text="You are already in the queue.")
                return

            await service.upsert_entry(
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
            entry = await service.get_entry(
                occurrence_id=occurrence.id,
                user_id=callback.from_user.id,
            )

            if entry is None:
                await callback.answer(text="You are not in the queue.")
                return

            if entry.is_done is True:
                await callback.answer(text="You are already done. Can't leave.")
                return

            await service.delete_last_user_entry(
                occurrence_id=occurrence.id,
                user_id=callback.from_user.id,
            )

        case callbacks.OccurrenceActionEnum.SKIP:
            entry = await service.get_entry(
                occurrence_id=occurrence.id,
                user_id=callback.from_user.id,
            )

            if entry is None:
                await callback.answer(text="You are not in the queue.")
                return

            if entry.is_done is True:
                await callback.answer(text="You are already done. Can't skip.")
                return

            entry.is_skipping = not entry.is_skipping
            await service.upsert_entry(entry=entry)

        case callbacks.OccurrenceActionEnum.DONE:
            entry = await service.get_entry(
                occurrence_id=occurrence.id,
                user_id=callback.from_user.id,
            )

            if entry is None:
                await callback.answer(text="You are not in the queue.")
                return

            if entry.is_done is True:
                await callback.answer(text="You are already done.")
                return

            entry.is_skipping = False
            entry.is_done = True
            await service.upsert_entry(entry=entry)

    event = await service.get_event(event_id=occurrence.event_id)
    if event is None:
        await callback.answer(text="Internal Error.")
        return

    chat = await service.get_chat(chat_id=event.chat_id)
    if chat is None:
        await callback.answer(text="Internal Error.")
        return

    entries = await service.get_entries(occurrence_id=occurrence.id)

    current_index = -1
    for index, entry in enumerate(entries):
        if entry.is_done is False and entry.is_skipping is False:
            current_index = index
            break

    date = occurrence.created_at.astimezone(tz=pytz.timezone(zone=chat.timezone))

    def decorize_entry(entry: schema.Entry, index: int) -> str:
        skip = "🆗 " if entry.is_done else "⬇️ " if entry.is_skipping else ""
        name = f"{entry.full_name}" + (f" (@{entry.username})" if entry.username else "")
        curr = " ⬅️" if index == current_index else ""
        return skip + name + curr

    text = (
        f"Event '{event.name}' starts on {date.strftime("%b %d %Y at %H:%M")}!\n"
        + (f"{event.description}\n" if event.description else "")
        + ("Current queue:\n" if len(entries) != 0 else "")
        + "\n".join(
            f"{index + 1}. {decorize_entry(entry, index)}" for index, entry in enumerate(entries)
        )
    )

    await bot.edit_message_text(
        text=text,
        chat_id=chat.id,
        message_id=occurrence.message_id,
        reply_markup=build_occurrence_keyboard(occurrence_id=occurrence.id),
    )

    await callback.answer(text="Success.")
