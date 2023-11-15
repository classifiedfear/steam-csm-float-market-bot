from typing import List, AnyStr, Tuple
import asyncio
from decimal import Decimal, localcontext

from bs4 import NavigableString, BeautifulSoup as bs

from telegram_bot.abc.providers import DataProvider
from telegram_bot.commands.bot_errors_command import InvalidName
from telegram_bot.resources.data_containers import SkinDataCsm


class CSMWikiDataProvider(DataProvider):
    def __init__(self, url_constructor, in_queue, out_queue) -> None:
        self._url_constructor = url_constructor
        self.in_queue = in_queue
        self.out_queue = out_queue

    async def get_processed_data(self) -> None:
        async for web_data in self.in_queue:
            soup = bs(web_data, 'lxml')
            await self._data_worker(soup)
        await self.out_queue.put(self.out_queue.SENTINEL)

    @staticmethod
    async def __find_elements(soup: bs, parent) -> List[NavigableString] | NavigableString:
        items = [item for item in soup.find_all(parent)]
        if len(items) == 1:
            return items[0]
        elif not items:
            raise InvalidName
        return items

    async def _data_worker(self, soup: bs) -> None:
        skin_name, qualities = await asyncio.gather(
            self.__find_elements(soup, 'title'),
            self.__find_elements(soup, 'th')
        )
        async with asyncio.TaskGroup() as tg:
            skin_name_data = tg.create_task(self.__get_correct_skin_name(skin_name.get_text()))
            quality_data = tg.create_task(self.__delete_duplicates(qualities))
        await self.out_queue.put(dict(skin_name=skin_name_data.result(), quality_data=quality_data.result()))

    @staticmethod
    async def __get_correct_skin_name(text: AnyStr) -> Tuple[AnyStr, AnyStr]:
        skin_name = text.partition('—')[0].partition('|')
        return skin_name[0].strip(), skin_name[2].strip()

    @staticmethod
    async def __delete_duplicates(iterable: list) -> List[AnyStr]:
        return list(set(text for item in iterable if (text := item.get_text()) != ''))


class CsmSkinDataProvider(DataProvider):
    def __init__(self, url_constructor, web, in_queue, out_queue):
        self._url_constructor = url_constructor
        self.in_queue = in_queue
        self.out_queue = out_queue
        self._web = web

    async def _data_worker(self, url_json_response: dict) -> None:
        tasks = []
        for skin_data in url_json_response['items']:
            coro = self.__work(skin_data)
            tasks.append(coro)
        await asyncio.gather(*tasks)

    async def __work(self, skin_data: dict) -> None:
        if (overpay := skin_data.get('overpay')) and (overpay_float := overpay.get('float')):
            price = await self._get_price(skin_data['assetId'])
            with localcontext() as context:
                context.prec = 4
                price_with_float = float(Decimal(price + overpay_float) * 1)

            await self.out_queue.put(SkinDataCsm(
                name=skin_data.get('fullName'),
                skin_float=float(skin_data.get('float')),
                price=price,
                price_with_float=price_with_float,
                overpay_float=overpay_float,
            ))

    async def _get_price(self, asset_id: int) -> float:
        price_json = await self._web.get_price(self._url_constructor.create_url_price(asset_id))
        price = price_json['defaultPrice']
        with localcontext() as context:
            price_with_csm_percent = price - (price / 100 * 8)
            context.prec = 4
            return float(Decimal(price_with_csm_percent) * 1)
