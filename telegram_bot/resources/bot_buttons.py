from typing import List, AnyStr

from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

from telegram_bot.resources import tg_const, settings


class BotButtons:
    def __init__(self):
        self.main_keyboard = self.create_keyboard(
                [
                    tg_const.button_find_skin_text, tg_const.button_find_skins_text, 'Показати список скінів доступних в базі',
                    tg_const.button_add_new_skin_db_text, tg_const.button_settings_text,
                    tg_const.button_desc_text,
                ])
        self.quality_settings_keyboard = self._get_quality_settings_keyboard()
        self.settings_keyboard = self.create_keyboard(
            [
                tg_const.search_db_msg_settings,
                tg_const.stattrak_msg_settings,
                tg_const.quality_msg_settings,
                'Повернутись до головного меню'
            ]
            )
        self.on_off_keyboard = self.create_keyboard(
            [tg_const.on, tg_const.off, tg_const.back_button_txt]
        )

    @staticmethod
    def create_keyboard(data: List[str] | str) -> ReplyKeyboardMarkup:
        builder = ReplyKeyboardBuilder()
        if isinstance(data, (list, tuple)):
            for element in data:
                builder.button(text=element)
        else:
            builder.button(text=data)
        builder.adjust(2)
        return builder.as_markup()

    @staticmethod
    def create_inline_keyboard(text: List[str] | str, url: AnyStr) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        if isinstance(text, (list, tuple)):
            for element in text:
                builder.button(text=element)
        else:
            builder.button(text=text, url=url)
        return builder.as_markup()

    def _get_quality_settings_keyboard(self):
        keyboard_list = [
            f'{key} ({value})' for key, value in zip(settings.Qualities.UKR.value, settings.Qualities.ENG.value)
        ]
        keyboard_list.append(tg_const.back_button_txt)
        return self.create_keyboard(keyboard_list)

