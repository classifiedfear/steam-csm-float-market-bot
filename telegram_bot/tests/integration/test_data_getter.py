import pytest

from telegram_bot.resources.matching_data_getter import CsmSteamMatchingDataGetter


@pytest.mark.asyncio
async def test_csm_steam_matching_data_getter():
    getter = CsmSteamMatchingDataGetter(
        weapon='Desert Eagle', skin='Code Red', quality='Battle-Scarred', stattrak=False
    )
    async for skin in getter.compare_all_data():
        print(skin)
