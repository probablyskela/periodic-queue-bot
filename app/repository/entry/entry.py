from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app import models, schema


class EntryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert(self, entry: schema.Entry) -> None:
        stmt = insert(models.Entry).values(self._map_entry_schema_to_model(entry=entry).to_dict())
        await self._session.execute(
            stmt.on_conflict_do_update(
                index_elements=["id"],
                set_=dict(stmt.excluded),
            ),
        )
        await self._session.commit()

    async def get(self, filter_: schema.EntryGetFilter) -> schema.Entry | None:
        stmt = select(models.Entry)

        if occurrence_id := filter_.get("occurrence_id"):
            stmt = stmt.where(models.Entry.occurrence_id == occurrence_id)
        if user_id := filter_.get("user_id"):
            stmt = stmt.where(models.Entry.user_id == user_id)

        entry = (await self._session.execute(stmt)).scalar_one_or_none()
        return self._map_entry_model_to_schema(entry=entry) if entry else None

    async def get_many(self, filter_: schema.EntryGetManyFilter) -> list[schema.Entry]:
        stmt = select(models.Entry)

        if occurrence_id := filter_.get("occurrence_id"):
            stmt = stmt.where(models.Entry.occurrence_id == occurrence_id)

        stmt = stmt.order_by(models.Entry.created_at.asc())

        entries = (await self._session.execute(stmt)).scalars().all()
        return [self._map_entry_model_to_schema(entry=entry) for entry in entries]

    async def delete(self, filter_: schema.EntryDeleteFilter) -> None:
        stmt = delete(models.Entry)

        if occurrence_id := filter_.get("occurrence_id"):
            stmt = stmt.where(models.Entry.occurrence_id == occurrence_id)
        if user_id := filter_.get("user_id"):
            stmt = stmt.where(models.Entry.user_id == user_id)

        await self._session.execute(stmt)
        await self._session.commit()

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
