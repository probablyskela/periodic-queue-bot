from functools import update_wrapper

import ring
from redis.asyncio import Redis as AsyncRedis

from app import schema
from app.config import config
from app.repository import Repository


class EventService:
    def __init__(self, repository: Repository, redis: AsyncRedis) -> None:
        self._repository = repository
        self._redis = redis

        self.get = update_wrapper(
            ring.aioredis(
                redis=redis,
                coder="pickle",
                expire=config.cache_ttl,
            )(self.get),
            self.get,
        )

    async def upsert(self, event: schema.Event) -> None:
        await self._repository.event.upsert(event=event)
        await self.get.delete(filter_=schema.EventGetFilter(id=event.id))

    async def get(self, filter_: schema.EventGetFilter) -> schema.Event | None:
        return await self._repository.event.get(filter_=filter_)

    async def delete(self, filter_: schema.EventDeleteFilter) -> None:
        await self._repository.event.delete(filter_=filter_)
