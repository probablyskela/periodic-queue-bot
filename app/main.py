import asyncio

import aiogram
import aiogram.filters

from app import callbacks, handlers, middlewares
from app.config import config


async def main() -> None:
    bot = aiogram.Bot(token=config.token)

    dp = aiogram.Dispatcher()
    dp.callback_query.middleware(middleware=middlewares.ServiceMiddleware())
    dp.message.middleware(middleware=middlewares.ServiceMiddleware())
    dp.message.register(
        handlers.configure_command_handler,
        aiogram.filters.Command("configure", prefix="/"),
    )
    dp.callback_query.register(
        handlers.occurrence_callback_handler,
        callbacks.OccurrenceCallbackFactory.filter(),
    )

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main=main())
