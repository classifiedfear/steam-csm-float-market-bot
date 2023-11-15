import asyncio
import logging
import os
import sys
from collections import deque

from aiogram import Dispatcher, Bot
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage
from apscheduler import AsyncScheduler
from apscheduler.datastores.sqlalchemy import SQLAlchemyDataStore

from redis import asyncio as aioredis

from telegram_bot.resources.bot_buttons import BotButtons
from telegram_bot.db.base import proceed_schemas, ENGINE, drop_all_tables

from telegram_bot.handlers import OtherHandler, OperationHandler, CommandHandler, SettingHandler, GeneralHandler


class Application:
    def __init__(self) -> None:
        self.buttons = BotButtons()
        self.redis = aioredis.Redis()
        self.dp = Dispatcher(storage=RedisStorage(self.redis))
        self.bot = Bot(token=os.getenv('token'), parse_mode=ParseMode.HTML)
        self.states = deque()

    async def __init_db(self) -> None:
        #await drop_all_tables(ENGINE)
        await proceed_schemas(ENGINE)

    async def __init_handlers(self, scheduler: AsyncScheduler) -> None:
        self.general_handler = GeneralHandler()
        self.general_handler.add(OperationHandler(
            self.bot, self.buttons, scheduler, self.states,
            redis=self.redis)).add(
            OtherHandler(
                self.buttons, self.states)).add(
            CommandHandler(
                self.redis, self.buttons)).add(
            SettingHandler(self.buttons, self.redis, self.states)
        )
        await self.general_handler.execute()

    async def main(self) -> None:
        await self.__init_db()
        data_store = SQLAlchemyDataStore(engine=ENGINE)
        async with AsyncScheduler(data_store=data_store) as scheduler:
            await self.__init_handlers(scheduler)
            self.dp.include_routers(*self.general_handler.router)
            await scheduler.start_in_background()
            await self.dp.start_polling(self.bot)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    app = Application()
    try:
        asyncio.run(app.main())
    except (KeyboardInterrupt, SystemExit):
        logging.info('Bot stopped!')
