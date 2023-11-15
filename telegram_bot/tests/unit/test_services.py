import asyncio
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

import pytest

from telegram_bot.tests.fixtures import queue
from telegram_bot.steam.services import SeleniumSteamDataService, ApiSteamDataService
from telegram_bot.steam.url_constructors import SkinSteamUrl, SkinSteamApiUrl

@pytest.mark.skip
@pytest.mark.asyncio
async def test_should_get_web_data_selenium(queue):
    url_const = SkinSteamUrl(weapon='USP-S', skin='Cortex', quality='Field-Tested', stattrak=False)
    web = SeleniumSteamDataService(url_const, queue)
    count = 0
    await web.add_web_data()
    async for data in queue:
        print(data)
        count += 1
    print(count)

@pytest.mark.skip
@pytest.mark.asyncio
async def test_should_run_few_instances_selenium_threadpool(queue):
    url_const = SkinSteamUrl(weapon='AK-47', skin='Asiimov', quality='Field-Tested', stattrak=False)
    url_const_2 = SkinSteamUrl(weapon='USP-S', skin='Cortex', quality='Field-Tested', stattrak=False)
    service = SeleniumSteamDataService(url_const, queue)
    service_2 = SeleniumSteamDataService(url_const_2, queue)

    async def proxy(service: SeleniumSteamDataService):
        await service.add_web_data()

    def pr(service: SeleniumSteamDataService):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(proxy(service))

    with ThreadPoolExecutor() as executor:
        executor.submit(pr, service)
        executor.submit(pr, service_2)

    async for skin in service.queue:
        assert skin is not None
        print(skin)
    async for item in service_2.queue:
        assert item is not None
        print(item)


@pytest.mark.skip
@pytest.mark.asyncio
async def test_should_run_few_instances_selenium_async(queue):
    url_const = SkinSteamUrl(weapon='AK-47', skin='Asiimov', quality='Field-Tested', stattrak=False)
    url_const_2 = SkinSteamUrl(weapon='USP-S', skin='Cortex', quality='Field-Tested', stattrak=False)
    service = SeleniumSteamDataService(url_const, queue)
    service_2 = SeleniumSteamDataService(url_const_2, queue)
    await asyncio.gather(service.add_web_data(), service_2.add_web_data())
    async for skin in service.queue:
        assert skin is not None
        print(skin)
    async for item in service_2.queue:
        assert item is not None
        print(item)


@pytest.mark.asyncio
async def test_should_get_web_data_api_steam_service(queue):
    url_const = SkinSteamApiUrl(weapon='AK-47', skin='Asiimov', quality='Field-Tested', stattrak=False)
    service = ApiSteamDataService(url_const, queue)
    await service.add_web_data()
    async for web_data in service.queue:
        print(web_data)
