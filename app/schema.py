import typing
import uuid
from datetime import datetime

import pytz
from pydantic import BaseModel, Field, ValidationInfo
from pydantic.functional_validators import AfterValidator, BeforeValidator

from app.config import config


class Period(BaseModel):
    years: str | None = None
    months: str | None = None
    weeks: str | None = None
    days: str | None = None
    hours: str | None = None
    minutes: str | None = None
    seconds: str | None = None


def validate_date(v: str | datetime | None, _: ValidationInfo) -> datetime | None:
    if v is None:
        return None
    if isinstance(v, datetime):
        if v.tzinfo is None:
            return v.replace(tzinfo=pytz.utc)
        return v.astimezone(tz=pytz.utc)
    return datetime.strptime(v, config.date_format).astimezone(tz=pytz.utc)


def validate_period(v: Period | None, _: ValidationInfo) -> Period | None:
    if v is None or all(v is None for v in v.model_dump().values()):
        return None
    return v


class EventInput(BaseModel):
    name: str
    description: str | None = None
    initial_date: typing.Annotated[datetime, BeforeValidator(validate_date)]
    periodicity: typing.Annotated[Period | None, AfterValidator(validate_period)] = None
    offset: typing.Annotated[Period | None, AfterValidator(validate_period)] = None
    times_occurred: int = 0


def validate_timezone(v: str, _: ValidationInfo) -> str | None:
    return pytz.timezone(zone=v).zone


class ConfigurationInput(BaseModel):
    timezone: typing.Annotated[str, AfterValidator(validate_timezone)] = "Etc/UTC"
    events: list[EventInput]


class Chat(BaseModel):
    id: int
    timezone: str
    config: dict[str, typing.Any]


class ChatGetFilter(typing.TypedDict, total=False):
    id: int


class Event(BaseModel):
    id: uuid.UUID = Field(default_factory=lambda: uuid.uuid4())
    chat_id: int
    name: str
    description: str | None = None
    initial_date: typing.Annotated[datetime, BeforeValidator(validate_date)]
    next_date: typing.Annotated[datetime, BeforeValidator(validate_date)]
    periodicity: typing.Annotated[Period | None, AfterValidator(validate_period)] = None
    offset: typing.Annotated[Period | None, AfterValidator(validate_period)] = None
    times_occurred: int = 0


class EventGetFilter(typing.TypedDict, total=False):
    id: uuid.UUID


class EventDeleteFilter(typing.TypedDict, total=False):
    chat_id: int


class Occurrence(BaseModel):
    id: uuid.UUID = Field(default_factory=lambda: uuid.uuid4())
    event_id: uuid.UUID
    message_id: int
    created_at: typing.Annotated[datetime, BeforeValidator(validate_date)]


class OccurrenceGetFilter(typing.TypedDict, total=False):
    id: uuid.UUID


class Entry(BaseModel):
    id: uuid.UUID = Field(default_factory=lambda: uuid.uuid4())
    occurrence_id: uuid.UUID
    full_name: str
    username: str | None
    user_id: int
    created_at: typing.Annotated[datetime, BeforeValidator(validate_date)]
    is_skipping: bool
    is_done: bool


class EntryGetFilter(typing.TypedDict, total=False):
    occurrence_id: uuid.UUID
    user_id: int


class EntryGetManyFilter(typing.TypedDict, total=False):
    occurrence_id: uuid.UUID


class EntryDeleteFilter(typing.TypedDict, total=False):
    occurrence_id: uuid.UUID
    user_id: int
