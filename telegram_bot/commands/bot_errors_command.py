from aiogram import types
from aiogram.fsm.context import FSMContext
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    TimeoutException,
    NoSuchWindowException
)

from telegram_bot.resources.bot_buttons import BotButtons
from telegram_bot.commands.abstact_command import BotCommand
from telegram_bot.resources import user_msg_const as user_msg


class InvalidWeapon(Exception):
    """Wrong weapon name"""


class InvalidSkin(Exception):
    """Wrong skin name"""


class InvalidName(Exception):
    """Wrong skin or weapon name"""


class StatTrakError(Exception):
    """Wrong type StatTrak"""


class RequestError(Exception):
    """Request error"""


class TechError(Exception):
    """Resource didn't load error"""


class ErrorsHandlerCommand(BotCommand):
    def __init__(self, error: Exception, message: types.Message, buttons: BotButtons, state: FSMContext):
        self.message = message
        self.state = state
        self.buttons = buttons
        self.error = error

    async def execute(self):
        await self.state.clear()
        match self.error:
            case TimeoutException():
                await self.message.answer(
                    user_msg.timeout_exception_error_text, reply_markup=self.buttons.main_keyboard
                )
                return True
            case (ElementClickInterceptedException(), NoSuchWindowException(), TechError()):
                await self.message.answer(user_msg.tech_error_text, reply_markup=self.buttons.main_keyboard)
                return True
            case StatTrakError():
                await self.message.answer(user_msg.stattrak_error_text, reply_markup=self.buttons.main_keyboard)
                return True
            case RequestError():
                await self.message.answer(user_msg.request_error_text, reply_markup=self.buttons.main_keyboard)
                return True
            case InvalidWeapon():
                await self.message.answer(user_msg.invalidweapon_error_text, reply_markup=self.buttons.main_keyboard)
                return True
            case InvalidSkin():
                await self.message.answer(user_msg.invalid_skin_error_text, reply_markup=self.buttons.main_keyboard)
                return True
            case InvalidName():
                await self.message.answer(user_msg.invalid_name_error_text, reply_markup=self.buttons.main_keyboard)
                return True

