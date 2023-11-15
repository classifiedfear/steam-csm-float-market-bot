import pytest

from telegram_bot.steam.providers import SeleniumSteamSkinDataProvider
from telegram_bot.steam.url_constructors import SkinSteamUrl
from telegram_bot.tests.fixtures import queue


@pytest.mark.asyncio
async def test_should_handle_data_from_provider(queue):
    url_constructor = SkinSteamUrl(weapon='USP-S', skin='Cortex', quality='Field-Tested', stattrak=False)
    in_queue = queue
    out_queue = queue
    await in_queue.put(
        {'skin_float': 'Float: 0.29906722903252\nPaint Seed: 541', 'price': '$2.68 USD', 'url': "javascript:BuyMarketListing('listing', '4455809658061103818', 730, '2', '34419661936')"}
    )
    await in_queue.put(in_queue.SENTINEL)
    provider = SeleniumSteamSkinDataProvider(url_constructor, in_queue, out_queue)
    await provider.get_processed_data()
    print(out_queue)

