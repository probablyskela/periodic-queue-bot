from unittest.mock import call

import pytest
from pytest_mock import MockerFixture

from app import schema
from app.repository import Repository
from app.service import Service


async def test_chat_service_upsert_success(
    mocker: MockerFixture,
    service: Service,
    repository: Repository,
    chat: schema.Chat,
) -> None:
    mocker.patch.object(repository.chat, "upsert", autospec=True)

    await service.chat.upsert(chat=chat)

    repository.chat.upsert.assert_awaited_once_with(chat=chat)


@pytest.fixture
def chat_service_get_mocks(
    mocker: MockerFixture,
    repository: Repository,
    chat: schema.Chat,
) -> None:
    mocker.patch.object(repository.chat, "get", return_value=chat, autospec=True)
    mocker.patch.object(repository.chat, "upsert", autospec=True)


async def test_chat_service_get_by_id_success(
    chat_service_get_mocks: None,
    service: Service,
    repository: Repository,
    chat: schema.Chat,
) -> None:
    filter_ = schema.ChatGetFilter(id=chat.id)

    result = await service.chat.get(filter_=filter_)

    repository.chat.get.assert_awaited_once_with(filter_=filter_)
    assert chat == result


async def test_chat_service_get_by_id_cache_create_success(
    chat_service_get_mocks: None,
    service: Service,
    repository: Repository,
    chat: schema.Chat,
) -> None:
    filter_ = schema.ChatGetFilter(id=chat.id)

    result1 = await service.chat.get(filter_=filter_)
    result2 = await service.chat.get(filter_=filter_)

    repository.chat.get.assert_awaited_once_with(filter_=filter_)
    assert chat == result1 == result2


async def test_chat_service_get_by_id_cache_delete_on_upsert_success(
    chat_service_get_mocks: None,
    mocker: MockerFixture,
    service: Service,
    repository: Repository,
    chat: schema.Chat,
) -> None:
    new_chat = chat.model_copy(update={"timezone": "Europe/Ukraine"}, deep=True)
    repository.chat.get.side_effect = [chat, new_chat]

    filter_ = schema.ChatGetFilter(id=chat.id)

    result1 = await service.chat.get(filter_=filter_)

    await service.chat.upsert(chat=new_chat)

    result2 = await service.chat.get(filter_=filter_)

    repository.chat.get.assert_has_awaits(
        [
            call(filter_=filter_),
            call(filter_=filter_),
        ],
    )
    assert chat == result1
    assert new_chat == result2
