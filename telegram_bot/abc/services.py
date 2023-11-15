import abc

from telegram_bot.abc.url_constructors import URLConstructor


class DataService(abc.ABC):
    @abc.abstractmethod
    async def add_web_data(self):
        pass
