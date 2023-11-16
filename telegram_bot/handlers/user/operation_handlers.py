from collections import deque

from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext

from aiogram.types import Message
from apscheduler import AsyncScheduler, ScheduleLookupError
from apscheduler.triggers.interval import IntervalTrigger
from redis.asyncio import Redis

from telegram_bot.abc.handlers import Handler
from telegram_bot.db.db_query import get_all_skin_from_db
from telegram_bot.resources.bot_buttons import BotButtons
from telegram_bot.commands.operation_commands import UserMsgParserCommand, DBParserCommand, UserMsgCommand
from telegram_bot.db.base import get_session_maker, ENGINE
from telegram_bot.db import db_query
from telegram_bot.midlewares.operations_middleware import GetterDefaultSettings
from telegram_bot.resources import tg_const, user_msg_const as user_msg
from telegram_bot.commands.bot_errors_command import ErrorsHandlerCommand
from telegram_bot.resources.misc import OperationStates


class OperationHandler(Handler):
    def __init__(
            self,
            bot: Bot,
            buttons: BotButtons,
            scheduler: AsyncScheduler,
            redis: Redis
    ):
        self.buttons = buttons
        self._init_router(redis)
        self.scheduler = scheduler
        self.bot = bot
        self.matched_skins_queue = deque()

    def _init_router(self, redis: Redis):
        self._router = Router()
        self._router.message.middleware(GetterDefaultSettings(redis))

    async def execute(self) -> None:
        await self._register_handlers()

    @property
    def router(self):
        return self._router

    async def _register_handlers(self) -> None:
        @self._router.message(F.text == 'Показати список скінів доступних в базі')
        async def selected_show_skins_in_db(message: Message) -> None:
            text = ''
            if item := await get_all_skin_from_db(get_session_maker(ENGINE)):
                for data in item:
                    weapon, skin = data
                    text += f'{weapon}, {skin}'
                    text += '\n'
                await message.answer(text)
            else:
                await message.answer('В базі немає данних.')

        @self._router.message(F.text == tg_const.button_find_skins_text)
        async def selected_find_skins_by_db(message: Message, state: FSMContext) -> None:
            await state.set_state(OperationStates.find_skin_by_db_state)
            await message.answer(
                'Почати пошук по базі данних?',
                reply_markup=self.buttons.create_keyboard([tg_const.on, tg_const.off, 'Повернутись до головного меню'])
            )

        @self._router.message(
            OperationStates.find_skin_by_db_state,
            F.text == tg_const.on
        )
        async def find_from_db_operation(message: Message, state: FSMContext) -> None:
            try:
                await self.scheduler.get_schedule(f"db_parser_task_{message.from_user.id}")
            except ScheduleLookupError:
                await state.clear()
                await message.answer('Пошук по базі розпочато!', reply_markup=self.buttons.main_keyboard)
                db_parser_command = DBParserCommand(self.matched_skins_queue)
                await self.scheduler.add_schedule(
                    db_parser_command.execute,
                    IntervalTrigger(minutes=7),
                    id=f"db_parser_task_{message.from_user.id}",
                    args=(db_parser_command,)
                )
            else:
                await message.answer('Пошук вже включений!')

        @self._router.message(OperationStates.find_skin_by_db_state, F.text == tg_const.off)
        async def cancel_find_skins_from_db_operation(message: Message, state: FSMContext):
            await message.answer(
                'Припиняю пошук по базі даних.',
                reply_markup=self.buttons.main_keyboard
            )

            await self.scheduler.remove_schedule(id=f"db_parser_task_{message.from_user.id}")
            await state.clear()

        @self._router.message(F.text == tg_const.button_add_new_skin_db_text)
        async def selected_add_new_skin_to_db(message: Message, state: FSMContext) -> None:
            await state.set_state(OperationStates.add_new_skin_by_db)
            await message.answer(
                user_msg.find_skin_button_desc,
                reply_markup=self.buttons.create_keyboard('Повернутись до головного меню')
            )

        @self._router.message(
            OperationStates.add_new_skin_by_db,
            F.text != tg_const.back_button_txt
        )
        async def add_new_skin_operation(message: Message, state: FSMContext, stattrak: bool, quality: str) -> None:
            user_msg_constructor = UserMsgCommand(message.text, stattrak_default=stattrak, quality_default=quality)
            try:
                weapon_data = await user_msg_constructor.execute()
                if await self._add_to_db_if_skin_exists(
                    weapon_data.weapon,
                    weapon_data.skin,
                    weapon_data.quality,
                    weapon_data.stattrak,
                    weapon_data.quality_data
                ):
                    await message.answer('Додано до бази!', reply_markup=self.buttons.main_keyboard)
                else:
                    await message.answer('Скін вже є в базі!')

            except Exception as error:
                error_handler_command = ErrorsHandlerCommand(error, message, self.buttons, state)
                is_handled = await error_handler_command.execute()
                if not is_handled:
                    raise

        @self._router.message(F.text == tg_const.button_find_skin_text)
        async def selected_find_skins_from_user_msg(message: Message, state: FSMContext) -> None:
            await state.set_state(OperationStates.find_skin_by_msg_state)
            await message.answer(
                user_msg.find_skin_button_desc,
                reply_markup=self.buttons.create_keyboard('Повернутись до головного меню')
            )

        @self._router.message(
            OperationStates.find_skin_by_msg_state,
            F.text != tg_const.back_button_txt
        )
        async def find_skins_from_user_msg(message: Message, state: FSMContext, stattrak: bool, quality: str) -> None:

            if (weapon_data := await self._execute_user_msg_finder(
                    message, state, stattrak, quality
            )).quality_data is None:
                await message.answer(user_msg.nothing_find_text)
            else:
                await self._add_to_db_if_skin_exists(*weapon_data)

            while self.matched_skins_queue:
                await self._show_data(self.matched_skins_queue.pop())
            else:
                await message.answer(user_msg.nothing_find_text)

    async def _show_data(self, skin):
        for user in await db_query.get_users(get_session_maker(ENGINE)):
            await self.bot.send_message(
                chat_id=user.user_id,
                text=tg_const.msg_with_skins_data.format(
                    weapon_name=(csm_skin := skin.get('csm_skin')).name,
                    steam_skin_float=(steam_skin := skin.get('steam_skin')).skin_float,
                    steam_price=steam_skin.price,
                    csm_skin_float=csm_skin.skin_float,
                    csm_price=csm_skin.price,
                    csm_price_with_float=csm_skin.price_with_float,
                    csm_overpay_float=csm_skin.overpay_float,
                    percent=skin.get('percent')),
                reply_markup=self.buttons.create_inline_keyboard(
                    text='Посилання на предмет',
                    url=steam_skin.link)
            )

    async def _indicate_user_about_parse_process(
            self, message: Message, weapon: str, skin: str, quality: str, stattrak: bool = None
    ):
        await message.answer(
            text=user_msg.msg_for_user_handling_data.format((
                f'{"Stattrak" if stattrak else "Standart"}, {weapon}, {skin}, {quality}')
            ),
            reply_markup=self.buttons.main_keyboard
        )

    async def _add_to_db_if_skin_exists(
            self, weapon: str, skin: str, quality: str, stattrak: bool, quality_data: tuple
    ):
        if not await db_query.is_skin_exists(
                get_session_maker(ENGINE),
                weapon=weapon,
                skin=skin,
                quality=quality,
                stattrak=stattrak
        ):
            await db_query.add_new_skin_to_db(
                get_session_maker(ENGINE),
                weapon,
                skin,
                stattrak,
                *quality_data
            )
            return True
        return False

    async def _execute_user_msg_constructor(self, message: Message, stattrak: bool, quality: str):
        user_msg_constructor = UserMsgCommand(message.text, stattrak, quality)
        weapon_data = await user_msg_constructor.execute()
        await self._indicate_user_about_parse_process(
            message,
            weapon_data.weapon,
            weapon_data.skin,
            weapon_data.quality,
            weapon_data.stattrak
        )
        return weapon_data

    async def _execute_user_msg_finder(self, message: Message, state: FSMContext, stattrak, quality):
        try:
            weapon_data = await self._execute_user_msg_constructor(message, stattrak, quality)
            await state.clear()

            user_msg_parser_command = UserMsgParserCommand(
                container=self.matched_skins_queue,
                weapon=weapon_data.weapon,
                skin=weapon_data.skin,
                quality=weapon_data.quality,
                stattrak=weapon_data.stattrak
            )

            await user_msg_parser_command.execute()
        except Exception as error:
            error_handler_command = ErrorsHandlerCommand(error, message, self.buttons, state)
            is_handled = await error_handler_command.execute()
            if not is_handled:
                raise
        else:
            return weapon_data
