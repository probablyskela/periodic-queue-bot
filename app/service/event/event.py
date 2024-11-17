from app import schema
from app.repository import Repository


class EventService:
    def __init__(self, repository: Repository) -> None:
        self._repository = repository

    async def upsert(self, event: schema.Event) -> None:
        await self._repository.event.upsert(event=event)

    async def get(self, filter_: schema.EventGetFilter) -> schema.Event | None:
        return await self._repository.event.get(filter_=filter_)

    async def delete(self, filter_: schema.EventDeleteFilter) -> None:
        await self._repository.event.delete(filter_=filter_)
