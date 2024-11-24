from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app import models, schema


class ChatRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert(self, chat: schema.Chat) -> None:
        stmt = insert(models.Chat).values(self._map_chat_schema_to_model(chat=chat).to_dict())
        await self._session.execute(
            stmt.on_conflict_do_update(
                index_elements=["id"],
                set_=dict(stmt.excluded),
            ),
        )
        await self._session.commit()

    async def get(self, filter_: schema.ChatGetFilter) -> schema.Chat | None:
        stmt = select(models.Chat)

        if id_ := filter_.get("id"):
            stmt = stmt.where(models.Chat.id == id_)

        chat = (await self._session.execute(stmt)).scalar_one_or_none()
        return chat.to_schema() if chat else None

    @staticmethod
    def _map_chat_schema_to_model(chat: schema.Chat) -> models.Chat:
        return models.Chat(
            id=chat.id,
            timezone=chat.timezone,
            config=chat.config,
        )
