import asyncio

import pytest
import pytest_unordered
from telegram_bot.resources.parser_factory import Parser
from telegram_bot.tests.fixtures import time_checker


@pytest.fixture()
def parser():
    def _method(name: str):
        parser = Parser(weapon='Desert Eagle', skin='Code Red', quality='Battle-Scarred', stattrak=False)
        return parser.create_parser(name)
    return _method


@pytest.mark.skip
@pytest.mark.asyncio
async def test_should_get_data_selenium_steam_data_provider(parser):
    selenium_parser = parser('selenium_steam')
    count = 0
    selenium_parser.run = time_checker(selenium_parser.run)
    result = await selenium_parser.run()
    for skin in result:
        assert isinstance(skin, tuple)
        print(skin)
        count += 1
    print(count)


@pytest.mark.asyncio
async def test_should_get_data_csm_wiki_parser(parser):
    csm_wiki_parser = parser('csm_wiki')
    csm_wiki_parser.run = time_checker(csm_wiki_parser.run)
    result = await csm_wiki_parser.run()
    for data in result:
        assert data is not None
        assert isinstance(data, dict)
        assert data.get('skin_name') == ('Desert Eagle', 'Code Red')
        assert pytest_unordered.unordered(data.get('quality_data')) == [
            'Field-Tested', 'Battle-Scarred', 'Well-Worn', 'Factory New', 'Minimal Wear'
        ]


@pytest.mark.asyncio
async def test_should_get_data_csm_parser(parser):
    csm_parser = parser('csm')
    csm_parser.run = time_checker(csm_parser.run)
    result = await csm_parser.run()
    for skin in result:
        assert isinstance(skin, tuple)
        print(skin)


@pytest.mark.skip
@pytest.mark.asyncio
async def test_should_get_data_api_steam_skin_data_provider(parser):
    api_steam = parser('api_steam')
    result = await api_steam.run()
    for skin in result:
        print(skin)
        assert isinstance(skin, tuple)


@pytest.mark.skip
@pytest.mark.asyncio
async def test_should_get_data_from_two_parsers(parser):
    selenium_steam = parser('selenium_steam')
    csm = parser('csm')
    result = await asyncio.gather(csm.run(), selenium_steam.run())
    for item in result:
        print(item)