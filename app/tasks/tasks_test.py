import uuid
from datetime import datetime

import aiogram
import aiogram.exceptions
import pytest
import pytz
from pytest_mock import MockerFixture
from redis.asyncio import Redis as AsyncRedis
from sqlalchemy.ext.asyncio import AsyncSession

from app import schema
from app.keyboards import build_occurrence_keyboard
from app.repository import Repository
from app.service import Service
from app.tasks.tasks import (
    resend_notification_message,
    resend_notification_message_task,
    send_notification_message,
    send_notification_message_task,
)
from app.util.util import RelativeDelta


@pytest.fixture
def repository(mocker: MockerFixture) -> Repository:
    return Repository(session=mocker.create_autospec(spec=AsyncSession))


@pytest.fixture
def service(repository: Repository, redis: AsyncRedis) -> Service:
    return Service(repository=repository, redis=redis)


@pytest.fixture
def bot(mocker: MockerFixture) -> aiogram.Bot:
    return mocker.create_autospec(spec=aiogram.Bot)


@pytest.fixture
def send_notification_message_mocks(
    mocker: MockerFixture,
    service: Service,
    event: schema.Event,
) -> None:
    mocker.patch.object(
        service.event,
        "get",
        return_value=event.model_copy(deep=True),
        autospec=True,
    )
    mocker.patch.object(service.occurrence, "upsert", autospec=True)
    mocker.patch.object(service.event, "upsert", autospec=True)
    mocker.patch.object(resend_notification_message_task, "apply_async", autospec=True)
    mocker.patch.object(send_notification_message_task, "apply_async", autospec=True)


async def test_send_notification_message_without_offset_success(
    send_notification_message_mocks: None,
    mocker: MockerFixture,
    service: Service,
    bot: aiogram.Bot,
    event: schema.Event,
    occurrence: schema.Occurrence,
) -> None:
    event.next_date = datetime.now(tz=pytz.utc) - RelativeDelta(minutes=5)
    event.periodicity = schema.Period(minutes="10")
    event.offset = None
    next_date = event.next_date + RelativeDelta(minutes=10)

    service.event.get.return_value = event.model_copy(deep=True)

    occurrence = schema.Occurrence(event=event, message_id=1, created_at=event.next_date)

    message = aiogram.types.Message(
        message_id=occurrence.message_id,
        date=datetime.now(tz=pytz.utc),
        chat=aiogram.types.Chat(id=event.chat.id, type="type"),
    )
    bot.send_message.return_value = message.model_copy(deep=True)

    mocker.patch.object(uuid, "uuid4", return_value=occurrence.id)

    await send_notification_message(service=service, bot=bot, event_id=event.id)

    service.event.get.assert_awaited_once_with(filter_=schema.EventGetFilter(id=event.id))
    bot.send_message.assert_awaited_once_with(
        chat_id=event.chat.id,
        text=service.occurrence.generate_notification_message_text(occurrence=occurrence),
        reply_markup=build_occurrence_keyboard(occurrence_id=occurrence.id),
    )
    resend_notification_message_task.apply_async.assert_not_called()

    event.next_date = next_date
    event.times_occurred += 1

    service.occurrence.upsert.assert_awaited_once_with(occurrence=occurrence)
    service.event.upsert.assert_awaited_once_with(event=event)
    send_notification_message_task.apply_async.assert_called_once_with(
        kwargs={"event_id": event.id},
        eta=next_date,
    )


async def test_send_notification_message_with_offset_success(
    send_notification_message_mocks: None,
    mocker: MockerFixture,
    service: Service,
    bot: aiogram.Bot,
    event: schema.Event,
    occurrence: schema.Occurrence,
) -> None:
    event.next_date = datetime.now(tz=pytz.utc) - RelativeDelta(minutes=5)
    event.periodicity = schema.Period(minutes="10")
    event.offset = schema.Period(minutes="2")
    next_date = event.next_date + RelativeDelta(minutes=10)

    service.event.get.return_value = event.model_copy(deep=True)

    occurrence = schema.Occurrence(event=event, message_id=1, created_at=event.next_date)

    message = aiogram.types.Message(
        message_id=occurrence.message_id,
        date=datetime.now(tz=pytz.utc),
        chat=aiogram.types.Chat(id=event.chat.id, type="type"),
    )
    bot.send_message.return_value = message.model_copy(deep=True)

    mocker.patch.object(uuid, "uuid4", return_value=occurrence.id)

    await send_notification_message(service=service, bot=bot, event_id=event.id)

    service.event.get.assert_awaited_once_with(filter_=schema.EventGetFilter(id=event.id))
    bot.send_message.assert_awaited_once_with(
        chat_id=event.chat.id,
        text=service.occurrence.generate_notification_message_text(occurrence=occurrence),
        reply_markup=build_occurrence_keyboard(occurrence_id=occurrence.id),
    )
    resend_notification_message_task.apply_async.assert_called_once_with(
        kwargs={"occurrence_id": occurrence.id},
        eta=event.next_date,
    )

    event.next_date = next_date
    event.times_occurred += 1

    service.occurrence.upsert.assert_awaited_once_with(occurrence=occurrence)
    service.event.upsert.assert_awaited_once_with(event=event)
    send_notification_message_task.apply_async.assert_called_once_with(
        kwargs={"event_id": event.id},
        eta=next_date - RelativeDelta(minutes=2),
    )


async def test_send_notification_message_event_not_found_failure(
    send_notification_message_mocks: None,
    mocker: MockerFixture,
    service: Service,
    bot: aiogram.Bot,
    event: schema.Event,
    occurrence: schema.Occurrence,
) -> None:
    service.event.get.return_value = None

    await send_notification_message(service=service, bot=bot, event_id=event.id)

    bot.send_message.assert_not_called()


@pytest.fixture
def resend_notification_message_mocks(
    mocker: MockerFixture,
    service: Service,
    occurrence: schema.Occurrence,
    entry: schema.Entry,
) -> None:
    mocker.patch.object(
        service.occurrence,
        "get",
        return_value=occurrence.model_copy(deep=True),
        autospec=True,
    )
    mocker.patch.object(service.entry, "get_many", return_value=[entry.model_copy(deep=True)])
    mocker.patch.object(service.occurrence, "upsert", autospec=True)


async def test_resend_notification_message_full_success(
    resend_notification_message_mocks: None,
    mocker: MockerFixture,
    service: Service,
    bot: aiogram.Bot,
    occurrence: schema.Occurrence,
    entry: schema.Entry,
) -> None:
    old_message_id = occurrence.message_id
    new_message_id = old_message_id + 1

    message = aiogram.types.Message(
        message_id=new_message_id,
        date=datetime.now(tz=pytz.utc),
        chat=aiogram.types.Chat(id=occurrence.event.chat.id, type="type"),
    )
    bot.send_message.return_value = message.model_copy(deep=True)

    await resend_notification_message(service=service, bot=bot, occurrence_id=occurrence.id)

    service.occurrence.get.assert_awaited_once_with(
        filter_=schema.OccurrenceGetFilter(id=occurrence.id),
    )
    service.entry.get_many.assert_awaited_once_with(
        filter_=schema.EntryGetManyFilter(occurrence_id=occurrence.id),
    )
    bot.delete_message.assert_awaited_once_with(
        chat_id=occurrence.event.chat.id,
        message_id=old_message_id,
    )
    bot.send_message.assert_awaited_once_with(
        chat_id=occurrence.event.chat.id,
        text=service.occurrence.generate_notification_message_text(
            occurrence=occurrence,
            entries=[entry],
        ),
        reply_markup=build_occurrence_keyboard(occurrence_id=occurrence.id),
    )

    occurrence.message_id = new_message_id
    service.occurrence.upsert.assert_awaited_once_with(occurrence=occurrence)


async def test_resend_notification_message_delete_message_throws_success(
    resend_notification_message_mocks: None,
    service: Service,
    bot: aiogram.Bot,
    occurrence: schema.Occurrence,
    entry: schema.Entry,
) -> None:
    old_message_id = occurrence.message_id
    new_message_id = old_message_id + 1

    message = aiogram.types.Message(
        message_id=new_message_id,
        date=datetime.now(tz=pytz.utc),
        chat=aiogram.types.Chat(id=occurrence.event.chat.id, type="type"),
    )
    bot.send_message.return_value = message.model_copy(deep=True)

    bot.delete_message.side_effect = aiogram.exceptions.TelegramBadRequest(
        method=aiogram.methods.DeleteMessage(
            chat_id=occurrence.event.chat.id,
            message_id=occurrence.message_id,
        ),
        message="Error",
    )

    await resend_notification_message(service=service, bot=bot, occurrence_id=occurrence.id)

    service.occurrence.get.assert_awaited_once_with(
        filter_=schema.OccurrenceGetFilter(id=occurrence.id),
    )
    service.entry.get_many.assert_awaited_once_with(
        filter_=schema.EntryGetManyFilter(occurrence_id=occurrence.id),
    )
    bot.delete_message.assert_awaited_once_with(
        chat_id=occurrence.event.chat.id,
        message_id=old_message_id,
    )
    bot.send_message.assert_awaited_once_with(
        chat_id=occurrence.event.chat.id,
        text=service.occurrence.generate_notification_message_text(
            occurrence=occurrence,
            entries=[entry],
        ),
        reply_markup=build_occurrence_keyboard(occurrence_id=occurrence.id),
    )

    occurrence.message_id = new_message_id
    service.occurrence.upsert.assert_awaited_once_with(occurrence=occurrence)


async def test_resend_notification_message_occurrence_not_found_failure(
    resend_notification_message_mocks: None,
    service: Service,
    bot: aiogram.Bot,
    occurrence: schema.Occurrence,
) -> None:
    service.occurrence.get.return_value = None

    await resend_notification_message(service=service, bot=bot, occurrence_id=occurrence.id)

    bot.send_message.assert_not_called()
