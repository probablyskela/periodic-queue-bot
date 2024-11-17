from app import schema
from app.repository import Repository


class ChatService:
    def __init__(self, repository: Repository) -> None:
        self._repository = repository

    async def upsert(self, chat: schema.Chat) -> None:
        await self._repository.chat.upsert(chat=chat)

    async def get(self, filter_: schema.ChatGetFilter) -> schema.Chat | None:
        return await self._repository.chat.get(filter_=filter_)
