from __future__ import annotations

from collections import deque

from redis.asyncio import Redis
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from telegram_bot.abc.handlers import Handler
from telegram_bot.resources.bot_buttons import BotButtons
from telegram_bot.midlewares.settings_check import SettingsCheck
from telegram_bot.resources import tg_const, user_msg_const as user_msg, settings
from telegram_bot.resources.misc import SettingStates


class SettingHandler(Handler):
    def __init__(self, buttons: BotButtons, redis: Redis):
        self._handlers = set()
        self.buttons = buttons
        self._router = Router()
        self.redis = redis
        self._router.message.middleware(SettingsCheck(self.redis))

    async def execute(self) -> None:
        await self._register_handlers()
        for handler in self._handlers:
            await handler.execute()

    async def _register_handlers(self) -> None:
        @self._router.message(F.text == tg_const.button_settings_text)
        async def general_settings(
                message: Message, state: FSMContext, stattrak: bool, quality: str, search: bool
        ) -> None:
            await state.set_state(SettingStates.choosing_settings_state)
            await message.answer(
                tg_const.settings_msg.format(
                    "".join(item[0] for item in zip(settings.Qualities.UKR.value, settings.Qualities.ENG.value)
                            if item[1] == quality),
                    "Включений" if stattrak else "Виключений",
                    "Включений" if search else "Виключений"
                ),
                reply_markup=self.buttons.settings_keyboard
            )

        @self._router.message(
            SettingStates.choosing_settings_state,
            lambda message: message.text in {
                tg_const.quality_msg_settings,
                tg_const.stattrak_msg_settings,
                tg_const.search_db_msg_settings
            } and message.text != 'Повернутись до головного меню'
        )
        async def choosing_a_certain_one_setting(message: Message, state: FSMContext) -> None:
            setting_state = None
            markup = None
            msg = None

            match message.text:
                case tg_const.quality_msg_settings:
                    setting_state = SettingStates.choosing_quality_state
                    markup = self.buttons.quality_settings_keyboard
                    msg = user_msg.choose_default_quality_msg
                case tg_const.search_db_msg_settings:
                    setting_state = SettingStates.choosing_search_state
                    markup = self.buttons.on_off_keyboard
                    msg = user_msg.choose_default_search_db_msg
                case tg_const.stattrak_msg_settings:
                    setting_state = SettingStates.choosing_stattrak_state
                    markup = self.buttons.on_off_keyboard
                    msg = user_msg.choose_default_stattrak_msg

            await state.set_state(setting_state)
            await message.answer(msg, reply_markup=markup)

        @self._router.message(
            SettingStates.choosing_stattrak_state,
            lambda message: message.text in {tg_const.on, tg_const.off} and message.text != tg_const.back_button_txt
        )
        async def set_stattrak_status(message: Message, state: FSMContext) -> None:
            if message.text != tg_const.back_button_txt:
                stattrak_setting = True if message.text == tg_const.on else False
                await self.redis.hset(
                        f'{message.from_user.id}_settings',
                        'stattrak',
                        value='1' if stattrak_setting else '0'
                    )
                await message.answer(
                    f'Зміни збережено! Stattrak: {"Включено" if stattrak_setting else "Виключено"}',
                    reply_markup=self.buttons.main_keyboard
                )

                await state.clear()

        @self._router.message(
            SettingStates.choosing_search_state,
            lambda message: message.text in {tg_const.on, tg_const.off} and message.text != tg_const.back_button_txt
        )
        async def set_search_by_db_after_user_searching(message: Message, state: FSMContext) -> None:
            if message.text != tg_const.back_button_txt:
                search_setting = True if message.text == tg_const.on else False
                await self.redis.hset(
                    f'{message.from_user.id}_settings',
                    'search',
                    value='1' if search_setting else '0'
                )
                await message.answer(
                    f'Зміни збережено! Пошук: {"Включено" if search_setting else "Виключено"}',
                    reply_markup=self.buttons.main_keyboard
                )

                await state.clear()

        @self._router.message(
            SettingStates.choosing_quality_state,
            lambda message: message.text in {
               f'{key} ({value})' for key, value in
               zip(settings.Qualities.UKR.value, settings.Qualities.ENG.value)
            } and message.text != tg_const.back_button_txt,
        )
        async def set_quality(message: Message, state: FSMContext) -> None:
            if message.text != tg_const.back_button_txt:
                quality_setting = message.text.split('(')[1][:-1].strip()
                await self.redis.hset(
                    f'{message.from_user.id}_settings',
                    'quality',
                    value=quality_setting
                )
                await message.answer(
                    f'Зміни збережено! Якість: {message.text}',
                    reply_markup=self.buttons.main_keyboard
                )
                await state.clear()
