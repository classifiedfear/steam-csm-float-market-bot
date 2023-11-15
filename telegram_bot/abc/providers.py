import asyncio
from abc import ABC, abstractmethod
from collections import namedtuple
from typing import AsyncIterable, Tuple

from telegram_bot.resources import steam_const


class DataProvider(ABC):
    _url_constructor = None
    in_queue = None
    out_queue = None

    async def get_processed_data(self):
        tasks = []
        async for web_data in self.in_queue:
            tasks.append(asyncio.create_task(self._data_worker(web_data)))
        await asyncio.gather(*tasks)
        await self.out_queue.put(self.out_queue.SENTINEL)

    @abstractmethod
    async def _data_worker(self, url_response: dict):
        pass


class SteamSkinDataProvider(DataProvider):
    @abstractmethod
    async def _data_worker(self, url_response: dict) -> AsyncIterable:
        pass

    async def _create_skin_link_steam(self, listing_id: int, app_id: int, context_id: int, skin_id: int) -> str:
        url_data = self._url_constructor.weapon_link_data
        link = steam_const.steam_market_link_csgo_full.format(
            steam_const.steam_web_root_csgo_all_market,
            '' if not url_data.stattrak else url_data.stattrak,
            url_data.weapon,
            url_data.skin,
            url_data.quality,
            int(listing_id),
            int(app_id),
            int(context_id),
            int(skin_id)
        )
        return link

