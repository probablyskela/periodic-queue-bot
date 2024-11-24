from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app import models, schema


class OccurrenceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert(self, occurrence: schema.Occurrence) -> None:
        stmt = insert(models.Occurrence).values(
            self._map_occurrence_schema_to_model(occurrence=occurrence).to_dict(),
        )
        await self._session.execute(
            stmt.on_conflict_do_update(
                index_elements=["id"],
                set_=dict(stmt.excluded),
            ),
        )
        await self._session.commit()

    async def get(self, filter_: schema.OccurrenceGetFilter) -> schema.Occurrence | None:
        stmt = select(models.Occurrence)

        if id_ := filter_.get("id"):
            stmt = stmt.where(models.Occurrence.id == id_)

        occurrence = (await self._session.execute(stmt)).scalar_one_or_none()
        return occurrence.to_schema() if occurrence else None

    @staticmethod
    def _map_occurrence_schema_to_model(occurrence: schema.Occurrence) -> models.Occurrence:
        return models.Occurrence(
            id=occurrence.id,
            event_id=occurrence.event.id,
            message_id=occurrence.message_id,
            created_at=occurrence.created_at.replace(tzinfo=None),
        )
