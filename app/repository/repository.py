import uuid

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app import models, schema


class Repository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert_chat(self, chat: schema.Chat) -> None:
        stmt = insert(models.Chat).values(self._map_chat_schema_to_model(chat=chat).to_dict())
        await self._session.execute(
            stmt.on_conflict_do_update(index_elements=["id"], set_=dict(stmt.excluded)),
        )
        await self._session.commit()

    async def get_chat(self, chat_id: int) -> schema.Chat | None:
        stmt = select(models.Chat).where(models.Chat.id == chat_id)
        chat = (await self._session.execute(stmt)).scalar_one_or_none()
        return self._map_chat_model_to_schema(chat=chat) if chat else None

    async def upsert_events(self, events: list[schema.Event]) -> None:
        if len(events) == 0:
            return
        stmt = insert(models.Event).values(
            [self._map_event_schema_to_model(event=event).to_dict() for event in events],
        )
        await self._session.execute(
            stmt.on_conflict_do_update(index_elements=["id"], set_=dict(stmt.excluded)),
        )
        await self._session.commit()

    async def get_event(self, event_id: uuid.UUID) -> schema.Event | None:
        stmt = select(models.Event).where(models.Event.id == event_id)
        event = (await self._session.execute(stmt)).scalar_one_or_none()
        return self._map_event_model_to_schema(event=event) if event else None

    async def delete_chat_events(self, chat_id: int) -> None:
        stmt = delete(models.Event).where(models.Event.chat_id == chat_id)
        await self._session.execute(stmt)
        await self._session.commit()

    async def insert_occurrence(self, occurrence: schema.Occurrence) -> None:
        stmt = insert(models.Occurrence).values(
            self._map_occurrence_schema_to_model(occurrence=occurrence).to_dict(),
        )
        await self._session.execute(stmt)
        await self._session.commit()

    async def get_occurrence(self, occurrence_id: uuid.UUID) -> schema.Occurrence | None:
        stmt = select(models.Occurrence).where(models.Occurrence.id == occurrence_id)
        occurrence = (await self._session.execute(stmt)).scalar_one_or_none()
        return self._map_occurrence_model_to_schema(occurrence=occurrence) if occurrence else None

    async def upsert_entry(self, entry: schema.Entry) -> None:
        stmt = insert(models.Entry).values(self._map_entry_schema_to_model(entry=entry).to_dict())
        await self._session.execute(
            stmt.on_conflict_do_update(index_elements=["id"], set_=dict(stmt.excluded)),
        )
        await self._session.commit()

    async def get_entry(self, occurrence_id: uuid.UUID, user_id: int) -> schema.Entry | None:
        stmt = select(models.Entry).where(
            models.Entry.occurrence_id == occurrence_id,
            models.Entry.user_id == user_id,
        )
        entry = (await self._session.execute(stmt)).scalar_one_or_none()
        return self._map_entry_model_to_schema(entry=entry) if entry else None

    async def get_entries(self, occurrence_id: uuid.UUID) -> list[schema.Entry]:
        stmt = (
            select(models.Entry)
            .where(models.Entry.occurrence_id == occurrence_id)
            .order_by(models.Entry.created_at.asc())
        )
        entries = (await self._session.execute(stmt)).scalars().all()
        return [self._map_entry_model_to_schema(entry=entry) for entry in entries]

    async def delete_last_user_entry(self, occurence_id: uuid.UUID, user_id: int) -> None:
        stmt = delete(models.Entry).where(
            models.Entry.id
            == select(models.Entry.id)
            .where(models.Entry.occurrence_id == occurence_id, models.Entry.user_id == user_id)
            .order_by(models.Entry.created_at.desc())
            .limit(1)
            .scalar_subquery(),
        )
        await self._session.execute(stmt)
        await self._session.commit()

    @staticmethod
    def _map_chat_schema_to_model(chat: schema.Chat) -> models.Chat:
        return models.Chat(
            id=chat.id,
            timezone=chat.timezone,
            config=chat.config,
        )

    @staticmethod
    def _map_chat_model_to_schema(chat: models.Chat) -> schema.Chat:
        return schema.Chat(
            id=chat.id,
            timezone=chat.timezone,
            config=chat.config,
        )

    @staticmethod
    def _map_event_schema_to_model(event: schema.Event) -> models.Event:
        return models.Event(
            id=event.id,
            chat_id=event.chat_id,
            name=event.name,
            description=event.description,
            initial_date=event.initial_date.replace(tzinfo=None),
            next_date=event.next_date.replace(tzinfo=None),
            offset_years=event.offset.years if event.offset else None,
            offset_months=event.offset.months if event.offset else None,
            offset_weeks=event.offset.weeks if event.offset else None,
            offset_days=event.offset.days if event.offset else None,
            offset_hours=event.offset.hours if event.offset else None,
            offset_minutes=event.offset.minutes if event.offset else None,
            offset_seconds=event.offset.seconds if event.offset else None,
            periodicity_years=event.periodicity.years if event.periodicity else None,
            periodicity_months=event.periodicity.months if event.periodicity else None,
            periodicity_weeks=event.periodicity.weeks if event.periodicity else None,
            periodicity_days=event.periodicity.days if event.periodicity else None,
            periodicity_hours=event.periodicity.hours if event.periodicity else None,
            periodicity_minutes=event.periodicity.minutes if event.periodicity else None,
            periodicity_seconds=event.periodicity.seconds if event.periodicity else None,
            times_occurred=event.times_occurred,
        )

    @staticmethod
    def _map_event_model_to_schema(event: models.Event) -> schema.Event:
        return schema.Event(
            id=event.id,
            chat_id=event.chat_id,
            name=event.name,
            description=event.description,
            initial_date=event.initial_date,
            next_date=event.next_date,
            offset=schema.Period(
                years=event.offset_years,
                months=event.offset_months,
                weeks=event.offset_weeks,
                days=event.offset_days,
                hours=event.offset_hours,
                minutes=event.offset_minutes,
                seconds=event.offset_seconds,
            ),
            periodicity=schema.Period(
                years=event.periodicity_years,
                months=event.periodicity_months,
                weeks=event.periodicity_weeks,
                days=event.periodicity_days,
                hours=event.periodicity_hours,
                minutes=event.periodicity_minutes,
                seconds=event.periodicity_seconds,
            ),
            times_occurred=event.times_occurred,
        )

    @staticmethod
    def _map_occurrence_schema_to_model(occurrence: schema.Occurrence) -> models.Occurrence:
        return models.Occurrence(
            id=occurrence.id,
            event_id=occurrence.event_id,
            message_id=occurrence.message_id,
            created_at=occurrence.created_at.replace(tzinfo=None),
        )

    @staticmethod
    def _map_occurrence_model_to_schema(occurrence: models.Occurrence) -> schema.Occurrence:
        return schema.Occurrence(
            id=occurrence.id,
            event_id=occurrence.event_id,
            message_id=occurrence.message_id,
            created_at=occurrence.created_at,
        )

    @staticmethod
    def _map_entry_schema_to_model(entry: schema.Entry) -> models.Entry:
        return models.Entry(
            id=entry.id,
            occurrence_id=entry.occurrence_id,
            username=entry.username,
            full_name=entry.full_name,
            user_id=entry.user_id,
            created_at=entry.created_at.replace(tzinfo=None),
            is_skipping=entry.is_skipping,
            is_done=entry.is_done,
        )

    @staticmethod
    def _map_entry_model_to_schema(entry: models.Entry) -> schema.Entry:
        return schema.Entry(
            id=entry.id,
            occurrence_id=entry.occurrence_id,
            username=entry.username,
            full_name=entry.full_name,
            user_id=entry.user_id,
            created_at=entry.created_at,
            is_skipping=entry.is_skipping,
            is_done=entry.is_done,
        )
