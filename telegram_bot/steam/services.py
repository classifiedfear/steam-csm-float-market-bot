from __future__ import annotations
import asyncio

from functools import wraps

from aiohttp import ClientSession
from selenium import webdriver
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.service import Service as EdgeService

from selenium.common.exceptions import (
    ElementClickInterceptedException,
    NoSuchElementException,
    ElementNotInteractableException
)
from fake_useragent import UserAgent

from telegram_bot.abc.services import DataService
from telegram_bot.abc.url_constructors import URLConstructor
from telegram_bot.resources import parse_const, steam_const
from telegram_bot.commands.bot_errors_command import InvalidWeapon, RequestError
from telegram_bot.resources.misc import ClosableQueue


def sleep_page(_func=None, *, sec_before: int | float = None, sec_after: int | float = None):
    def sleep_page_decorator(func):
        @wraps(func)
        async def wrapper_sleep(*args, **kwargs):
            if sec_before:
                await asyncio.sleep(sec_before)
            await func(*args, **kwargs)
            if sec_after:
                await asyncio.sleep(sec_after)
        return wrapper_sleep
    if _func is None:
        return sleep_page_decorator
    else:
        return sleep_page_decorator(_func)


class SeleniumSteamDataService(DataService):
    def __init__(self, url_constructor: URLConstructor, queue: ClosableQueue) -> None:
        self.url_constructor = url_constructor
        self.service = EdgeService(parse_const.driver_root_edge)
        self.options = EdgeOptions()
        for extension in parse_const.extensions:
            self.options.add_extension(extension)
        # self.options.add_argument(parse_const.headless_browser)
        self.options.add_argument(f'user-agent={UserAgent.random}')
        self.queue = queue
        self._url = self.url_constructor.create_url()

    async def add_web_data(self) -> None:
        with webdriver.Edge(self.options, self.service) as self._driver:
            await self._prep_vpn()
            await self._steam_market_prep_page()
            try:
                while page := await self._current_page():
                    if page == 1:
                        await self._find_accept_button()
                    await self._service_worker()
                    if page == 3 or not await self._steam_market_next_page(page):
                        break
            finally:
                await self.queue.put(self.queue.SENTINEL)

    @sleep_page(sec_before=2, sec_after=2)
    async def _prep_vpn(self) -> None:
        self._driver.get('chrome-extension://adlpodnneegcnbophopdmhedicjbcgco/popup.html')
        accept_button = self._driver.find_element(By.CLASS_NAME, 'analytics__button')
        accept_button.click()
        vpn_button = self._driver.find_element(By.CLASS_NAME, 'connect-button')
        vpn_button.click()

    async def _service_worker(self) -> None:

        prices_from_page = (
            item.text for item in self._driver.find_elements(By.CLASS_NAME, steam_const.get_price_for_item)
        )
        links_to_buy = (
            item.get_attribute('href') for item in self._driver.find_elements(
                By.CLASS_NAME, steam_const.get_link_for_item)
        )
        skins_float = (
            item.text for item in self._driver.execute_script(steam_const.float_checker_get_float)
        )

        for data in zip(skins_float, prices_from_page, links_to_buy):
            await self.queue.put({
                'skin_float': data[0],
                'price': data[1],
                'url': data[2],
            })

    @sleep_page(sec_after=2)
    async def _steam_market_prep_page(self) -> None:
        self._driver.get(self._url)

        length_page_selector = self._driver.execute_script(
            parse_const.float_checker_select_menu
        )
        length_page_selector.click()

        select_length = self._driver.execute_script(
            parse_const.float_checker_select_index
            .format(parse_const.float_checker_select_menu)
        )
        select_length.click()

        await self._steam_market_has_exceptions()

    @sleep_page(sec_before=5)
    async def _find_accept_button(self) -> None:
        try:
            accept_all_button = self._driver.find_element(By.ID, 'acceptAllButton')
            accept_all_button.click()
        except (NoSuchElementException, ElementNotInteractableException):
            pass

    async def _steam_market_has_exceptions(self) -> None:
        try:

            if error := self._driver.find_element(
                    By.CLASS_NAME, 'error_ctn'
            ).find_element(By.TAG_NAME, 'h3'):
                raise RequestError(error.text)

            if (error := self._driver.find_element(
                    By.ID, 'searchResultsTable'
            ).find_element(
                    By.CLASS_NAME, 'market_listing_table_message')):
                raise InvalidWeapon(error.text)
        except NoSuchElementException:
            return

    async def _steam_market_next_page(self, active_page: int) -> bool:
        if active_page == 'one_page':
            return False
        next_page = self._driver.find_element(By.ID, parse_const.button_for_next_page)
        if next_page.get_attribute('class') == 'pagebtn disabled':
            return False
        second_limit = 0

        while await self._current_page() == active_page:
            try:
                next_page.click()
            except (ElementNotInteractableException, ElementClickInterceptedException):
                return False
            await asyncio.sleep(2)
            second_limit += 2
            if second_limit > 20:
                return False
        return True

    async def _current_page(self) -> str | int:
        results_links = self._driver.find_element(By.ID, 'searchResults_links')
        active_page = results_links.find_element(By.CLASS_NAME, 'active')
        try:
            active_page_number = int(active_page.text)
        except ValueError:
            active_page_number = 'one_page'
        return active_page_number


class ApiSteamDataService(DataService):
    def __init__(self, url_constructor: URLConstructor, queue: ClosableQueue):
        self._url_constructor = url_constructor
        self.queue = queue

    async def add_web_data(self) -> None:
        page_number = 1
        start = 0
        count = 100
        tasks = []
        async with ClientSession() as session:
            while page_number <= 3:
                self._url_constructor.start, self._url_constructor.offset = start, count
                url = self._url_constructor.create_url()
                tasks.append(asyncio.create_task(session.get(
                    url, headers={'user-agent': f'{UserAgent.random}'}, proxy='http://51.38.191.151:80'))
                )
                start += count
                page_number += 1
            responses = await asyncio.gather(*tasks)
            for resp in responses:
                await self.queue.put(await resp.json(content_type=None))
        await self.queue.put(self.queue.SENTINEL)
