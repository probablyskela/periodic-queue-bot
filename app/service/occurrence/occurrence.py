from app import schema
from app.repository import Repository


class OccurrenceService:
    def __init__(self, repository: Repository) -> None:
        self._repository = repository

    async def upsert(self, occurrence: schema.Occurrence) -> None:
        await self._repository.occurrence.upsert(occurrence=occurrence)

    async def get(self, filter_: schema.OccurrenceGetFilter) -> schema.Occurrence | None:
        return await self._repository.occurrence.get(filter_=filter_)
