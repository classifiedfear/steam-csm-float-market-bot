import asyncio
import logging
import struct
from typing import AsyncIterable, Tuple, List

from csgo.client import CSGOClient
from steam.client import SteamClient

from telegram_bot.abc.url_constructors import URLConstructor
from telegram_bot.commands.bot_errors_command import RequestError
from telegram_bot.abc.providers import SteamSkinDataProvider
from telegram_bot.resources.data_containers import SkinDataSteam, ParamsSkinData
from telegram_bot.resources.misc import ClosableQueue

logging.basicConfig(format='[%(asctime)s] %(levelname)s %(name)s: %(message)s', level=logging.DEBUG)


class ApiSteamSkinDataProvider(SteamSkinDataProvider):
    def __init__(self, url_const: URLConstructor, in_queue: ClosableQueue, out_queue: ClosableQueue):
        self._url_constructor = url_const
        self.in_queue = in_queue
        self.out_queue = out_queue
        self.steam_client = SteamClient()
        self.steam_client.login('devsayder', 'rv9up0ax', two_factor_code='HF2KV')
        self.cs_game_coordinator = CSGOClient(self.steam_client)

    async def get_processed_data(self) -> None:
        try:
            self.cs_game_coordinator.launch()
            self.cs_game_coordinator.wait_event('ready', timeout=1)
            async for web_data in self.in_queue:
                await self._data_worker(web_data)
        finally:
            await self.out_queue.put(self.out_queue.SENTINEL)
            self.cs_game_coordinator.exit()
            self.steam_client.logout()

    async def _data_worker(self, url_response: dict) -> None:
        if url_response is None:
            raise RequestError

        listing = url_response['listinginfo']

        async for data in self.__find_data(listing):
            self.cs_game_coordinator.request_preview_data_block(
                s=int(data.param_s),
                a=int(data.param_a),
                d=int(data.param_d),
                m=int(data.param_m)
            )
            try:
                response = self.cs_game_coordinator.wait_event('item_data_block', 10)

                skin_float = struct.unpack('<f', struct.pack('<I', response[0].paintwear))
                skin_seed = response[0].paintseed

                await self.out_queue.put(SkinDataSteam(
                    price=data.price,
                    skin_float=skin_float[0],
                    link=data.link_to_buy,
                    skin_seed=skin_seed,
                ))
            except TypeError:
                pass

    @staticmethod
    async def __get_converted_price(converted_price_per_unit: str, converted_fee_per_unit: str) -> float:
        return float(str(
            price := converted_price_per_unit + converted_fee_per_unit)[0:-2] + '.' + str(price)[-2:]
            )

    @staticmethod
    async def _get_steam_skin_params(valuable_skin_data_link: str) -> Tuple[int, int, int, int]:
        id_from_link = valuable_skin_data_link.replace(
            'steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20', ''
        ).split('A')
        if id_from_link[0].startswith('S'):
            param_s = int(id_from_link[0].replace('S', ''))
            param_m = 0
        else:
            param_m = int(id_from_link[0].replace('M', ''))
            param_s = 0
        params_a_b = id_from_link[1].split('D')
        param_a = int(params_a_b[0].replace('A', ''))
        param_d = int(params_a_b[1].replace('D', ''))
        return param_m, param_s, param_a, param_d

    async def __find_data(self, listing: dict) -> AsyncIterable[ParamsSkinData]:
        for value in listing.values():
            asset = value['asset']

            listing_id = value['listingid']

            app_id = asset['appid']

            context_id = asset['contextid']

            asset_id = asset['id']

            inspect_link: str = (
                asset.get('market_actions')[0].get('link').replace('%listingid%', listing_id).replace(
                    '%assetid%', asset_id
                )
            )

            param_m, param_s, param_a, param_d = await self._get_steam_skin_params(inspect_link)

            link_to_buy = await self._create_skin_link_steam(
                int(listing_id),
                int(app_id),
                int(context_id),
                int(param_a)
            )

            price = await self.__get_converted_price(
                value['converted_price_per_unit'], value['converted_fee_per_unit']
            )

            yield ParamsSkinData(link_to_buy, price, param_m, param_s, param_d, param_a)


class SeleniumSteamSkinDataProvider(SteamSkinDataProvider):
    def __init__(self, url_const: URLConstructor, in_queue: ClosableQueue, out_queue: ClosableQueue):
        self._url_constructor = url_const
        self.in_queue = in_queue
        self.out_queue = out_queue

    async def __work(self, url, float_data, price) -> None:
        link_data = self._get_link_data(url)
        async with asyncio.TaskGroup() as tg:
            url = tg.create_task(self._create_skin_link_steam(*link_data))

            float_seed = tg.create_task(self._get_skin_float_and_seed(float_data))

            skin_price = tg.create_task(self._get_skin_price(price))

        float_seed = float_seed.result()

        await self.out_queue.put(SkinDataSteam(
            price=skin_price.result(),
            skin_float=float_seed[0],
            skin_seed=float_seed[1],
            link=url.result(),
        ))

    async def _data_worker(self, url_response: dict) -> None:
        float_data = url_response['skin_float']
        price = url_response['price']
        url = url_response['url']

        await self.__work(url, float_data, price)

    @staticmethod
    def _get_link_data(url: str) -> List[str]:
        return ''.join(url.split()[1:]).replace("'", '').replace(")", '').split(',')

    @staticmethod
    async def _get_skin_float_and_seed(skin_valuable_data: str) -> Tuple[float, int]:
        item_split = skin_valuable_data.split('\n')
        skin_float = item_split[0].split(': ')[1].split()[0]
        skin_seed = item_split[1].split(': ')[1]
        return float(skin_float), int(skin_seed)

    @staticmethod
    async def _get_skin_price(price: str) -> float | bool:
        if price == 'sold':
            return False
        value = float(''.join(char for char in price.replace(',', '') if char.isdigit() or char == '.'))
        print(value)
        return value
