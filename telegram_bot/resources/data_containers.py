from typing import NamedTuple


class WeaponLinkData(NamedTuple):
    weapon: str
    skin: str
    quality: str
    stattrak: str | bool


class SkinDataCsm(NamedTuple):
    name: str
    skin_float: float
    price: float
    price_with_float: float
    overpay_float: float


class SkinDataSteam(NamedTuple):
    price: float
    skin_float: float
    link: str
    skin_seed: int


class ParamsSkinData(NamedTuple):
    link_to_buy: str
    price: float
    param_m: int
    param_s: int
    param_d: int
    param_a: int
