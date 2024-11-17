from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import models, schema
from app.repository import Repository


async def test_chat_repository_upsert_insert_success(
    db_session: AsyncSession,
    repository: Repository,
) -> None:
    chat_id = 1
    timezone = "Europe/Kyiv"
    configuration = {"timezone": "Europe/Kyiv", "events": []}

    chat = schema.Chat(
        id=chat_id,
        timezone=timezone,
        config=configuration,
    )

    await repository.chat.upsert(chat=chat)

    assert (
        await db_session.execute(
            select(models.Chat).where(
                models.Chat.id == chat.id,
                models.Chat.timezone == chat.timezone,
            ),
        )
    ).scalar_one_or_none() is not None


async def test_chat_repository_upsert_update_success(
    db_session: AsyncSession,
    repository: Repository,
) -> None:
    chat_id = 1
    timezone = "Europe/Kyiv"
    configuration = {"timezone": "Europe/Kyiv", "events": []}

    chat = schema.Chat(
        id=chat_id,
        timezone=timezone,
        config=configuration,
    )

    await repository.chat.upsert(chat=chat)

    assert (
        await db_session.execute(
            select(models.Chat).where(
                models.Chat.id == chat.id,
                models.Chat.timezone == chat.timezone,
            ),
        )
    ).scalar_one_or_none() is not None

    chat.timezone = "Etc/UTC"

    await repository.chat.upsert(chat=chat)

    assert (
        await db_session.execute(
            select(models.Chat).where(
                models.Chat.id == chat.id,
                models.Chat.timezone == chat.timezone,
            ),
        )
    ).scalar_one_or_none() is not None


async def test_chat_repository_get_by_id_success(repository: Repository) -> None:
    chat = schema.Chat(
        id=1,
        timezone="Europe/Kyiv",
        config={"timezone": "Europe/Kyiv", "events": []},
    )

    await repository.chat.upsert(chat=chat)

    new_chat = await repository.chat.get(filter_=schema.ChatGetFilter(id=chat.id))

    assert chat == new_chat
