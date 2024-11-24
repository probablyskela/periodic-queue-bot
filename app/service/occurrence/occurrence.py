from datetime import datetime
from functools import update_wrapper

import pytz
import ring
from redis.asyncio import Redis as AsyncRedis

from app import schema
from app.config import config
from app.repository import Repository


class OccurrenceService:
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

    async def upsert(self, occurrence: schema.Occurrence) -> None:
        await self._repository.occurrence.upsert(occurrence=occurrence)
        await self.get.delete(filter_=schema.OccurrenceGetFilter(id=occurrence.id))

    async def get(self, filter_: schema.OccurrenceGetFilter) -> schema.Occurrence | None:
        return await self._repository.occurrence.get(filter_=filter_)

    def generate_notification_message_text(
        self,
        occurrence: schema.Occurrence,
        entries: list[schema.Entry] | None = None,
    ) -> str:
        entries = entries or []

        event, chat = occurrence.event, occurrence.event.chat

        current_index = -1
        for index, entry in enumerate(entries):
            if entry.is_done is False and entry.is_skipping is False:
                current_index = index
                break

        def decorize_entry(entry: schema.Entry, index: int) -> str:
            nonlocal current_index

            skip = "🆗 " if entry.is_done else "⬇️ " if entry.is_skipping else ""
            name = f"{entry.full_name}" + (f" (@{entry.username})" if entry.username else "")
            curr = " ⬅️" if index == current_index else ""
            return skip + name + curr

        timezone = pytz.timezone(zone=chat.timezone)
        date = occurrence.created_at.astimezone(tz=timezone)
        date_str = (
            date.strftime("%A, %b %d at %H:%M:%S")
            if datetime.now(tz=timezone).year == date.year
            else date.strftime("%A, %b %d, %Y at %H:%M:%S")
        )

        return (
            f"{event.name} starts on {date_str}!\n"
            + (f"{event.description}\n" if event.description is not None else "")
            + ("Current queue:\n" if entries else "")
            + "\n".join(
                f"{index + 1}. {decorize_entry(entry, index)}"
                for index, entry in enumerate(entries)
            )
        )
