import abc

from telegram_bot.resources.data_containers import WeaponLinkData


class URLConstructor(abc.ABC):
    def __init__(self,  weapon: str, skin: str, quality: str, stattrak: bool, *args, **kwargs):
        self.weapon = weapon
        self.skin = skin
        self.quality = quality
        self.stattrak = stattrak

    @staticmethod
    def _params(url: str, params: dict) -> str:
        url += '?'
        for key, item in params.items():
            url += f'{key}={item}&'
        return url[:-1]

    @property
    @abc.abstractmethod
    def weapon_link_data(self) -> WeaponLinkData:
        pass

    @abc.abstractmethod
    def create_url(self) -> str:
        pass
