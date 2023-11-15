from telegram_bot.abc.url_constructors import URLConstructor
from telegram_bot.resources import steam_const
from telegram_bot.resources.data_containers import WeaponLinkData


class SkinSteamUrl(URLConstructor):
    def __init__(self, weapon: str, skin: str, quality: str, stattrak: bool) -> None:
        super().__init__(weapon, skin, quality, stattrak)

    @property
    def weapon_link_data(self) -> WeaponLinkData:
        stattrak: str = 'StatTrak\u2122%20' if self.stattrak else None
        weapon: str = '%20'.join(self.weapon.split()) + '%20%7C%20'
        skin: str = '%20'.join(self.skin.split()) + '%20%28'
        if ('Factory New' or 'Minimal Wear') in self.quality:
            quality: str = '%20'.join(self.quality.split()) + '%29'
        else:
            quality: str = self.quality + '%29'
        return WeaponLinkData(weapon=weapon, skin=skin, quality=quality, stattrak=stattrak)

    def create_url(self) -> str:
        data = self.weapon_link_data
        url: str = (
            f'{steam_const.steam_web_root_csgo_all_market}'
            f'{"" if not data.stattrak else data.stattrak}'
            f'{data.weapon}'
            f'{data.skin}'
            f'{data.quality}'
         )
        return url


class SkinSteamApiUrl(SkinSteamUrl):
    def __init__(self, weapon: str, skin: str, quality: str, stattrak: bool, *, start: int = 0, offset: int = 10):
        super().__init__(weapon, skin, quality, stattrak)
        self.start = start
        self.offset = offset

    def create_url(self) -> str:
        url = super().create_url()
        url += '/render/'
        params: dict = {
            'start': self.start,
            'count': self.offset,
            'currency': 1
        }
        return self._params(url, params)
