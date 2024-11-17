from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app import models, schema


class EventRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert(self, event: schema.Event) -> None:
        stmt = insert(models.Event).values(self._map_event_schema_to_model(event=event).to_dict())
        await self._session.execute(
            stmt.on_conflict_do_update(
                index_elements=["id"],
                set_=dict(stmt.excluded),
            ),
        )
        await self._session.commit()

    async def get(self, filter_: schema.EventGetFilter) -> schema.Event | None:
        stmt = select(models.Event)

        if id_ := filter_.get("id"):
            stmt = stmt.where(models.Event.id == id_)

        event = (await self._session.execute(stmt)).scalar_one_or_none()
        return self._map_event_model_to_schema(event=event) if event else None

    async def delete(self, filter_: schema.EventDeleteFilter) -> None:
        stmt = delete(models.Event)

        if chat_id := filter_.get("chat_id"):
            stmt = stmt.where(models.Event.chat_id == chat_id)

        await self._session.execute(stmt)
        await self._session.commit()

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
