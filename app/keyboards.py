import uuid

import aiogram
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app import callbacks


def build_occurrence_keyboard(occurrence_id: uuid.UUID) -> aiogram.types.InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="Join Queue",
        callback_data=callbacks.OccurrenceCallbackFactory(
            action=callbacks.OccurrenceActionEnum.JOIN,
            occurrence_id=occurrence_id,
        ),
    )
    builder.button(
        text="Leave Queue",
        callback_data=callbacks.OccurrenceCallbackFactory(
            action=callbacks.OccurrenceActionEnum.LEAVE,
            occurrence_id=occurrence_id,
        ),
    )
    builder.button(
        text="Skip / Unskip",
        callback_data=callbacks.OccurrenceCallbackFactory(
            action=callbacks.OccurrenceActionEnum.SKIP,
            occurrence_id=occurrence_id,
        ),
    )
    builder.button(
        text="Done / Undone",
        callback_data=callbacks.OccurrenceCallbackFactory(
            action=callbacks.OccurrenceActionEnum.DONE,
            occurrence_id=occurrence_id,
        ),
    )
    builder.adjust(2, 2)
    return builder.as_markup()
