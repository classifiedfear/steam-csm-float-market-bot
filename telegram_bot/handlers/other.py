from __future__ import annotations

from collections import deque

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from telegram_bot.abc.handlers import Handler
from telegram_bot.resources.bot_buttons import BotButtons
from telegram_bot.resources import tg_const
from telegram_bot.resources.misc import SettingStates


class OtherHandler(Handler):
    def __init__(self, buttons: BotButtons, states: deque):
        self.buttons = buttons
        self._router = Router()
        self.states = states

    async def execute(self) -> None:
        await self.__register_handlers()

    async def __register_handlers(self) -> None:
        @self._router.message(F.text == tg_const.back_to_main_menu_bot_txt)
        async def back_to_main_manu(message: Message, state: FSMContext) -> None:
            await message.answer(
                tg_const.back_button_txt,
                reply_markup=self.buttons.main_keyboard
            )
            await state.clear()
            return

        @self._router.message(F.text == tg_const.back_button_txt)
        async def back(message: Message, state: FSMContext) -> None:
            #if len(self.states) == 1:
            #    self.states.clear()
            #    await message.answer(
            #        tg_const.back_to_main_menu_bot_txt,
            #        reply_markup=self.buttons.main_keyboard
            #    )
            #    await state.clear()
            #    return
#
            #state_, markup = self.states[0]
            #del self.states[1]
            #await message.answer(
            #    'Повертаюсь назад',
            #    reply_markup=markup
            #)
            #await state.set_state(state_)



            if await state.get_state() == SettingStates.choosing_settings_state:
                await message.answer(
                    tg_const.back_to_main_menu_bot_txt,
                    reply_markup=self.buttons.main_keyboard
                )
                await state.clear()
            else:
                await message.answer(
                    'Повертаюсь назад',
                    reply_markup=self.buttons.settings_keyboard
                )
                await state.set_state(SettingStates.choosing_settings_state)
