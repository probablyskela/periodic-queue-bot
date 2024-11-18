import json
import logging

import aiogram
from pydantic import ValidationError

from app import schema
from app.service import Service

logger = logging.getLogger(__name__)


async def configure_command_handler(
    message: aiogram.types.Message,
    bot: aiogram.Bot,
    service: Service,
) -> None:
    if message.document is None:
        await message.reply("Please attach configuration file.")
        return

    try:
        file = await bot.get_file(file_id=message.document.file_id)
        if file.file_path is None:
            await message.reply("Failed to load configuration file. Please try again.")
            return
        data = await bot.download_file(file_path=file.file_path)
    except TypeError:
        await message.reply("Failed to load configuration file. Please try again.")
        return
    if data is None:
        await message.reply("Failed to load configuration file. Please try again.")
        return

    try:
        obj = json.load(data)
    except ValueError:
        await message.reply("Failed to load configuration. Invalid json format.")
        return

    try:
        configuration = schema.ConfigurationInput.model_validate(obj=obj)
    except ValidationError:
        await message.reply("Failed to load configuration. Invalid config format.")
        return

    try:
        await service.load_configuration(
            chat_id=message.chat.id,
            configuration=configuration,
            configuration_raw=obj,
        )
    except Exception:
        logger.exception("failed to load configuration.")
        await message.reply("Failed to load configuration. Internal error.")
        return

    await message.reply("Configuration loaded successfully.")
