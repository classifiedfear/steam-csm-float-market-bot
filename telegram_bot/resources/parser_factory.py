import asyncio
from typing import AsyncIterable, Any, List

from telegram_bot.csm.providers import CsmSkinDataProvider, CSMWikiDataProvider
from telegram_bot.csm.services import ResponseCSMWikiDataService, ResponseCSMDataService
from telegram_bot.csm.url_constructors import SkinsCSMWikiUrl, SkinsCsmUrl
from telegram_bot.resources.misc import ClosableQueue

from telegram_bot.steam.providers import ApiSteamSkinDataProvider, SeleniumSteamSkinDataProvider
from telegram_bot.steam.services import SeleniumSteamDataService, ApiSteamDataService
from telegram_bot.steam.url_constructors import SkinSteamUrl, SkinSteamApiUrl


class ParserInterface:
    _url_constructor = None
    _web = None
    _provider = None

    def __init__(self):
        self.service_queue = ClosableQueue()
        self.done_queue = ClosableQueue()

    async def run(self) -> List[Any]:
        await asyncio.gather(self._web.add_web_data(), self._provider.get_processed_data())
        return [data async for data in self.done_queue]


class CsmWikiSteamParser(ParserInterface):
    def __init__(self, weapon: str, skin: str, quality: str, stattrak: bool):
        super().__init__()
        self._url_constructor = SkinsCSMWikiUrl(weapon, skin, quality, stattrak)
        self._web = ResponseCSMWikiDataService(self._url_constructor, self.service_queue)
        self._provider = CSMWikiDataProvider(self._url_constructor, self.service_queue, self.done_queue)


class CsmSteamParser(ParserInterface):
    def __init__(self, weapon: str, skin: str, quality: str, stattrak: bool):
        super().__init__()
        self._url_constructor = SkinsCsmUrl(weapon, skin, quality, stattrak)
        self._web = ResponseCSMDataService(self._url_constructor, self.service_queue)
        self._provider = CsmSkinDataProvider(self._url_constructor, self._web, self.service_queue, self.done_queue)


class SeleniumSteamParser(ParserInterface):
    def __init__(self, weapon: str, skin: str, quality: str, stattrak: bool):
        super().__init__()
        self._url_constructor = SkinSteamUrl(weapon, skin, quality, stattrak)
        self._web = SeleniumSteamDataService(self._url_constructor, self.service_queue)
        self._provider = SeleniumSteamSkinDataProvider(self._url_constructor, self.service_queue, self.done_queue)
        

class ApiSteamParser(ParserInterface):
    def __init__(self, weapon: str, skin: str, quality: str, stattrak: bool):
        super().__init__()
        self._url_constructor = SkinSteamApiUrl(weapon, skin, quality, stattrak)
        self._web = ApiSteamDataService(self._url_constructor, self.service_queue)
        self._provider = ApiSteamSkinDataProvider(self._url_constructor, self.service_queue, self.done_queue)


class Parser:
    _registry: dict = {}

    def __init__(self, weapon: str, skin: str, quality: str, stattrak: bool):

        self.weapon: str = weapon
        self.skin: str = skin
        self.quality: str = quality
        self.stattrak: bool = stattrak
        self._init_parsers()

    def _init_parsers(self) -> None:
        self._registry['csm_wiki'] = CsmWikiSteamParser
        self._registry['csm'] = CsmSteamParser
        self._registry['selenium_steam'] = SeleniumSteamParser
        self._registry['api_steam'] = ApiSteamParser

    def create_parser(self, parser: str) -> ParserInterface:
        class_ = self._registry[parser]
        return class_(self.weapon, self.skin, self.quality, self.stattrak)


