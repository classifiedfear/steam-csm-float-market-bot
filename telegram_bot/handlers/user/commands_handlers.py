from redis.asyncio import Redis
from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message

from telegram_bot.abc.handlers import Handler
from telegram_bot.resources.bot_buttons import BotButtons
from telegram_bot.midlewares.register_check import RegisterCheck

from telegram_bot.resources import user_msg_const as user_msg, tg_const


class CommandHandler(Handler):
    def __init__(
            self, redis: Redis, buttons: BotButtons
    ):
        self.buttons = buttons
        self._router = Router()
        self._router.message.middleware.register(RegisterCheck(redis))

    @property
    def router(self):
        return self._router

    async def execute(self) -> None:
        await self.__register_handlers()

    async def __register_handlers(self) -> None:
        @self._router.message(F.text == tg_const.button_desc_text)
        async def command_help(message: Message) -> None:
            await message.answer(tg_const.HELP)

        @self._router.message((F.text == tg_const.button_help_text))
        async def command_desc(message: Message) -> None:
            await message.answer(user_msg.description_for_user)

        @self._router.message(CommandStart())
        async def command_start(message: Message) -> None:
            await message.answer(
                text=user_msg.hello_user_msg.format(message.from_user.full_name),
                reply_markup=self.buttons.main_keyboard
            )


