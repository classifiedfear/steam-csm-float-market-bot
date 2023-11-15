from __future__ import annotations

from aiohttp import ClientResponse, ClientSession
from fake_useragent import UserAgent
from json.decoder import JSONDecodeError

from telegram_bot.abc.services import DataService
from telegram_bot.abc.url_constructors import URLConstructor
from telegram_bot.resources.misc import ClosableQueue


class ResponseCSMWikiDataService(DataService):
    def __init__(self, url_constructor: URLConstructor, queue: ClosableQueue) -> None:
        super().__init__()
        self.url_constructor = url_constructor
        self.queue = queue

    async def add_web_data(self):
        async with ClientSession() as session:
            async with session.get(
                    self.url_constructor.create_url(), headers={'user-agent': f'{UserAgent.random}'}) as response:
                await self.queue.put(await response.text())
        await self.queue.put(self.queue.SENTINEL)


class ResponseCSMDataService(DataService):
    def __init__(self, url_constructor: URLConstructor, queue: ClosableQueue) -> None:
        super().__init__()
        self.url_constructor = url_constructor
        self.queue = queue

    async def add_web_data(self):
        offset = 0
        page_size = 60
        async with ClientSession() as session:
            while True:
                self.url_constructor.offset = offset
                url = self.url_constructor.create_url()
                async with session.get(
                        url, headers={'user-agent': f'{UserAgent.random}'}
                ) as response:
                    if not await self._response_check(response):
                        break
                offset += page_size
            await self.queue.put(self.queue.SENTINEL)

    async def _response_check(self, response: ClientResponse) -> bool:
        try:
            web_data = await response.json(content_type=None)
            if web_data.get('error'):
                return False
            else:
                await self.queue.put(web_data)
        except JSONDecodeError:
            pass
        return True

    async def get_price(self, url: str):
        async with ClientSession() as session:
            async with session.get(url, headers={'user-agent': f'{UserAgent.random}'}) as response:
                return await response.json(content_type=None)
