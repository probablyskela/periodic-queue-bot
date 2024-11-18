import typing
import uuid
from datetime import datetime

from sqlalchemy import BIGINT, JSON, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Chat(Base):
    __tablename__ = "chat"

    id: Mapped[int] = mapped_column(BIGINT, primary_key=True)
    timezone: Mapped[str]

    config: Mapped[dict[str, typing.Any]] = mapped_column(JSON)

    def to_dict(self) -> dict[str, typing.Any]:
        return {
            "id": self.id,
            "timezone": self.timezone,
            "config": self.config,
        }


class Event(Base):
    __tablename__ = "event"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    chat_id: Mapped[int] = mapped_column(ForeignKey("chat.id", ondelete="CASCADE"))

    name: Mapped[str]
    description: Mapped[str | None]

    initial_date: Mapped[datetime]
    next_date: Mapped[datetime]

    periodicity_years: Mapped[str | None]
    periodicity_months: Mapped[str | None]
    periodicity_weeks: Mapped[str | None]
    periodicity_days: Mapped[str | None]
    periodicity_hours: Mapped[str | None]
    periodicity_minutes: Mapped[str | None]
    periodicity_seconds: Mapped[str | None]

    offset_years: Mapped[str | None]
    offset_months: Mapped[str | None]
    offset_weeks: Mapped[str | None]
    offset_days: Mapped[str | None]
    offset_hours: Mapped[str | None]
    offset_minutes: Mapped[str | None]
    offset_seconds: Mapped[str | None]

    times_occurred: Mapped[int]

    def to_dict(self) -> dict[str, typing.Any]:
        return {
            "id": self.id,
            "chat_id": self.chat_id,
            "name": self.name,
            "description": self.description,
            "initial_date": self.initial_date,
            "next_date": self.next_date,
            "periodicity_years": self.periodicity_years,
            "periodicity_months": self.periodicity_months,
            "periodicity_weeks": self.periodicity_weeks,
            "periodicity_days": self.periodicity_days,
            "periodicity_hours": self.periodicity_hours,
            "periodicity_minutes": self.periodicity_minutes,
            "periodicity_seconds": self.periodicity_seconds,
            "offset_years": self.offset_years,
            "offset_months": self.offset_months,
            "offset_weeks": self.offset_weeks,
            "offset_days": self.offset_days,
            "offset_hours": self.offset_hours,
            "offset_minutes": self.offset_minutes,
            "offset_seconds": self.offset_seconds,
            "times_occurred": self.times_occurred,
        }


class Occurrence(Base):
    __tablename__ = "occurrence"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    event_id: Mapped[uuid.UUID]
    message_id: Mapped[int] = mapped_column(BIGINT)
    created_at: Mapped[datetime]

    def to_dict(self) -> dict[str, typing.Any]:
        return {
            "id": self.id,
            "event_id": self.event_id,
            "message_id": self.message_id,
            "created_at": self.created_at,
        }


class Entry(Base):
    __tablename__ = "entry"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    occurrence_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("occurrence.id", ondelete="CASCADE"),
    )
    full_name: Mapped[str]
    username: Mapped[str | None]
    user_id: Mapped[int] = mapped_column(BIGINT)
    created_at: Mapped[datetime]

    is_skipping: Mapped[bool]
    is_done: Mapped[bool]

    def to_dict(self) -> dict[str, typing.Any]:
        return {
            "id": self.id,
            "occurrence_id": self.occurrence_id,
            "username": self.username,
            "full_name": self.full_name,
            "user_id": self.user_id,
            "is_skipping": self.is_skipping,
            "is_done": self.is_done,
            "created_at": self.created_at,
        }
