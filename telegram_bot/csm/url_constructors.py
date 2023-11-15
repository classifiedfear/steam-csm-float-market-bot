from telegram_bot.abc.url_constructors import URLConstructor
from telegram_bot.resources import csm_const
from telegram_bot.resources.data_containers import WeaponLinkData


class SkinsCsmUrl(URLConstructor):
    def __init__(self, weapon: str, skin: str, quality: str, stattrak: bool, *, offset: int = 0) -> None:
        super().__init__(weapon, skin, quality, stattrak)
        self.offset = offset

    @property
    def weapon_link_data(self) -> WeaponLinkData:
        skin: str = '%20'.join(self.skin.split())
        weapon: str = '%20'.join(self.weapon.split())
        quality: str = ''.join(
            csm_const.WEAPON_QUALITY_CSM_WIKI[item] for item in csm_const.WEAPON_QUALITY_CSM_WIKI.keys()
            if item in self.quality
        )
        stattrak: str = 'true' if self.stattrak else 'false'
        return WeaponLinkData(weapon=weapon, skin=skin, quality=quality, stattrak=stattrak)

    def create_url(self) -> str:
        def_params = {
            'hasTradeLock': 'false',
            'isStatTrak': (weapon_data := self.weapon_link_data).stattrak,
            'limit': 60,
            'name': f"{weapon_data.weapon}%20{weapon_data.skin}",
            'offset': self.offset,
            'order': 'asc',
            'priceWithBonus': 35,
            'quality': weapon_data.quality,
            'sort': 'float',
            'withStack': 'true'
        }
        return self._params(csm_const.url_csm_base, def_params)

    def create_url_price(self, asset_id: int):
        params = {
            'appId': 730,
            'id': asset_id,
            'isBot': 'true',
            'botInventory': 'true'
        }
        return self._params(csm_const.url_csm_skin_info_base, params)


class SkinsCSMWikiUrl(URLConstructor):
    @property
    def weapon_link_data(self) -> WeaponLinkData:
        weapon = self.weapon.lower().replace(' ', '-')
        skin = self.skin.lower().replace("'", '').replace(' ', '-')
        return WeaponLinkData(weapon=weapon, skin=skin, quality=self.quality, stattrak=self.stattrak)

    def create_url(self) -> str:
        return f'{csm_const.url_csm_wiki}/{self.weapon_link_data.weapon}/{self.weapon_link_data.skin}'
