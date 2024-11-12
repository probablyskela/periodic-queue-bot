import enum
import uuid

from aiogram.filters.callback_data import CallbackData


class OccurrenceActionEnum(enum.Enum):
    JOIN = "JOIN"
    LEAVE = "LEAVE"
    SKIP = "SKIP"
    DONE = "DONE"


class OccurrenceCallbackFactory(CallbackData, prefix="join_queue"):
    action: OccurrenceActionEnum
    occurrence_id: uuid.UUID
