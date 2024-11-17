from pytest_mock import MockerFixture

from app import schema
from app.repository import Repository
from app.service import Service


async def test_chat_service_upsert_success(
    mocker: MockerFixture,
    service: Service,
    repository: Repository,
) -> None:
    spy_repository_chat_upsert = mocker.patch.object(repository.chat, "upsert")

    chat = schema.Chat(
        id=1,
        timezone="Europe/Kyiv",
        config={"timezone": "Europe/Kyiv", "events": []},
    )

    await service.chat.upsert(chat=chat)

    spy_repository_chat_upsert.assert_awaited_once_with(chat=chat)


async def test_chat_service_get_by_id_success(
    mocker: MockerFixture,
    service: Service,
    repository: Repository,
) -> None:
    spy_repository_chat_get = mocker.patch.object(repository.chat, "get")

    filter_ = schema.ChatGetFilter(id=1)

    chat = await service.chat.get(filter_=filter_)

    spy_repository_chat_get.assert_awaited_once_with(filter_=filter_)
    assert chat == spy_repository_chat_get.return_value
