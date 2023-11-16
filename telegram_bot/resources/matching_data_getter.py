import abc
import asyncio
import bisect
from collections import deque
from typing import AsyncGenerator, Tuple, AsyncIterable
from operator import itemgetter
from decimal import Decimal, localcontext

from selenium.common import NoSuchElementException

from telegram_bot.resources.parser_factory import Parser, ParserInterface


class MatchingDataGetter(metaclass=abc.ABCMeta):
    def __init__(self, weapon: str, skin: str, quality: str, stattrak: bool):
        self.weapon: str = weapon
        self.skin: str = skin
        self.quality: str = quality
        self.stattrak: bool = stattrak
        self.matched_data = deque()

    @abc.abstractmethod
    async def factory_method(self, *args, **kwargs):
        pass

    async def compare_all_data(self) -> AsyncIterable[dict] | None:
        parser_site_1, parser_site_2 = await self.factory_method()

        parser_site_1_task = await parser_site_1.run()
        if not parser_site_1_task:
            return

        parser_site_2_task = await parser_site_2.run()

        async for matched_skin in self._get_matched_data(parser_site_1_task, parser_site_2_task):
            yield matched_skin

    async def _get_matched_data(self, parser_site_1_data, parser_site_2_data) -> AsyncGenerator:
        for steam_skin in parser_site_2_data:
            tasks = []
            for csm_skin in parser_site_1_data:
                coro = self._comparing_data(steam_skin, csm_skin, parser_site_1_data)
                tasks.append(coro)
            await asyncio.gather(*tasks)
            if self.matched_data:
                yield await self._find_matched_data()
            else:
                continue

    async def _find_matched_data(self):
        max_percent_skin = max(self.matched_data, key=itemgetter('percent'))
        self.matched_data.clear()
        return max_percent_skin

    async def _comparing_data(self, skin_data_1, skin_data_2, pop_list):
        with localcontext() as context:
            context.prec = 2
            steam_float = Decimal(skin_data_1.skin_float) * 1
            csm_float = Decimal(skin_data_2.skin_float) * 1
            if steam_float == csm_float:
                percent = 100 - ((skin_data_1.price * 100) // skin_data_2.price_with_float)
                if percent >= 15:
                    self.matched_data.append(
                        {
                            'steam_skin': skin_data_1,
                            'csm_skin': pop_list.pop(bisect.bisect_left(pop_list, skin_data_2)),
                            'percent': percent
                        }
                    )


class CsmSteamMatchingDataGetter(MatchingDataGetter):
    async def factory_method(self) -> Tuple[ParserInterface, ParserInterface]:
        parser_factory = Parser(self.weapon, self.skin, self.quality, self.stattrak)
        return (
            parser_factory.create_parser('csm'),
            parser_factory.create_parser('selenium_steam')
        )

