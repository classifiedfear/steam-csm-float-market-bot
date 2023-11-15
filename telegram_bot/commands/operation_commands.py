import bisect
from abc import abstractmethod
from collections import namedtuple, deque

from telegram_bot.commands.abstact_command import BotCommand
from telegram_bot.db.base import get_session_maker, ENGINE
from telegram_bot.db import db_query
from telegram_bot.resources.parser_factory import Parser
from telegram_bot.resources import settings
from telegram_bot.resources.matching_data_getter import CsmSteamMatchingDataGetter
from telegram_bot.commands.bot_errors_command import InvalidWeapon, InvalidSkin


class BotParserCommands(BotCommand):
    def __init__(self, container: deque):
        self.container = container

    @abstractmethod
    async def execute(self):
        pass

    async def _parse_data(self, weapon: str, skin: str, quality: str, stattrak: bool):
        matching_data_provider = CsmSteamMatchingDataGetter(weapon, skin, quality, stattrak)
        async for item in matching_data_provider.compare_all_data():
            self.container.append(item)


class UserMsgCommand(BotCommand):
    def __init__(self, msg: str, stattrak_default: bool = False, quality_default: str = 'Field-Tested'):
        self._user_weapon_msg = [item.strip() for item in msg.lower().split(',')]
        self.stattrak_default = stattrak_default
        self.quality_default = quality_default

    async def execute(self) -> namedtuple:
        weapon, skin, quality, stattrak = await self._construct_weapon_data_from_user_msg()

        if weapon is None:
            raise InvalidWeapon

        if skin is None:
            raise InvalidSkin

        if quality is None:
            quality = self.quality_default

        if stattrak is None:
            stattrak = self.stattrak_default

        weapon_data = await self._get_correct_skin_data(weapon, skin, quality, stattrak)

        return weapon_data

    @staticmethod
    async def _get_correct_skin_data(weapon: str, skin: str, quality: str, stattrak: bool):
        """Check if skin exists, if exists return correct name for data and qualities for that skin."""
        parser = Parser(weapon, skin, quality, stattrak)
        skin_wiki = parser.create_parser('csm_wiki')

        result = await skin_wiki.run()
        for data in result:
            weapon, skin = data.get('skin_name')

            correct_skin_data = namedtuple('CorrectSkinData', 'weapon, skin, quality, stattrak, quality_data')

            return correct_skin_data(
                weapon=weapon,
                skin=skin,
                quality=quality,
                stattrak=stattrak,
                quality_data=data.get('quality_data')
            )

    async def _construct_weapon_data_from_user_msg(self):
        weapon = None
        skin = None
        quality = None
        stattrak = None

        for index, item in enumerate(self._user_weapon_msg.copy()):
            if item in settings.WEAPONS:
                weapon = item
                self._user_weapon_msg.remove(item)
            elif item in [data.lower() for data in settings.Qualities.ENG.value]:
                quality = item
                self._user_weapon_msg.remove(item)
            elif item == 'stattrak':
                self._user_weapon_msg.remove(item)
                stattrak = True
            else:
                skin = item
                self._user_weapon_msg.remove(item)

        return weapon, skin, quality, stattrak


class UserMsgParserCommand(BotParserCommands):
    def __init__(
            self,
            weapon: str,
            skin: str,
            quality: str,
            stattrak: bool,
            container: deque,
    ) -> None:
        super().__init__(container=container)
        self.weapon = weapon
        self.skin = skin
        self.quality = quality
        self.stattrak = stattrak

    async def execute(self):
        await self._parse_data(self.weapon, self.skin, self.quality, self.stattrak)


class DBParserCommand(BotParserCommands):
    def __init__(self, container: deque):
        super().__init__(container=container)

    async def execute(self):
        if weapon_data := await db_query.get_random_weapon_from_db(
                get_session_maker(ENGINE)
        ):
            await self._parse_data(weapon_data[0], weapon_data[1], weapon_data[2], weapon_data[3])


