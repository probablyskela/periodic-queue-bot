from app import schema
from app.repository import Repository


class EntryService:
    def __init__(self, repository: Repository) -> None:
        self._repository = repository

    async def upsert(self, entry: schema.Entry) -> None:
        await self._repository.entry.upsert(entry=entry)

    async def get(self, filter_: schema.EntryGetFilter) -> schema.Entry | None:
        return await self._repository.entry.get(filter_=filter_)

    async def get_many(self, filter_: schema.EntryGetManyFilter) -> list[schema.Entry]:
        return await self._repository.entry.get_many(filter_=filter_)

    async def delete(self, filter_: schema.EntryDeleteFilter) -> None:
        await self._repository.entry.delete(filter_=filter_)
