from functools import update_wrapper

import ring
from redis.asyncio import Redis as AsyncRedis

from app import schema
from app.config import config
from app.repository import Repository


class ChatService:
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

    def __ring_key__(self) -> str:
        return "chat_service"

    async def upsert(self, chat: schema.Chat) -> None:
        await self._repository.chat.upsert(chat=chat)
        await self.get.delete(filter_=schema.ChatGetFilter(id=chat.id))

    async def get(self, filter_: schema.ChatGetFilter) -> schema.Chat | None:
        return await self._repository.chat.get(filter_=filter_)
