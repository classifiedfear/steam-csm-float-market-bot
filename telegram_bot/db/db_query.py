import asyncio
from typing import Callable, Type, Tuple, Any

from sqlalchemy import select, func, ScalarResult, Row, and_, delete
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.dialects.postgresql import insert

from telegram_bot.db.skins_model import Skin, StatTrak, Weapon, Quality, SteamSkinData
from telegram_bot.db.user_models import User


async def remove_user(async_session: async_sessionmaker, user_id: int):
    async with async_session() as session:
        stmt = delete(User).where(User.user_id == user_id)
        await session.execute(stmt)
        await session.commit()


async def add_user(async_session: async_sessionmaker, user_id: int, username: str, full_name: str):
    async with async_session() as session:
        await session.execute(insert(User).values(user_id=user_id, username=username, full_name=full_name))
        await session.commit()


async def is_user_exists(async_session: async_sessionmaker, user_id: int) -> bool:
    async with async_session() as session:
        stmt = select(User.full_name).where(User.user_id == user_id)
        sql_result = await session.execute(stmt)
        result = sql_result.one_or_none()
        return True if result else False


async def get_user_info(
        async_session: async_sessionmaker, user_id: int, information: str | list | tuple
) -> Type[Any] | None:
    async with async_session() as session:
        if isinstance(information, (list, tuple)):
            models = [User.__dict__[info] for info in information]
            stmt = select(*models).where(User.user_id == user_id)
        else:
            stmt = select(User.__dict__[information]).where(User.user_id == user_id)

        result = await session.execute(stmt)
        return result.one_or_none()


async def get_users(async_session: async_sessionmaker):
    async with async_session() as session:
        stmt = select(User)
        result = await session.execute(stmt)
        return result.scalars()


async def is_skin_exists(
        async_session: async_sessionmaker, weapon: str, skin: str, quality: str, stattrak: bool
) -> ScalarResult[Skin] | None:
    async with async_session() as session:
        stmt = (
            select(Skin.skin_name, Weapon.weapon_name, Quality.quality_title, StatTrak.stattrak_status)
            .join(Skin.weapons)
            .join(Skin.qualities)
            .join(Skin.stattraks)
            .where(and_(
                Skin.skin_name == skin,
                Weapon.weapon_name == weapon,
                Quality.quality_title == quality,
                StatTrak.stattrak_status == stattrak,
            ))
        )
        sql_result = await session.execute(stmt)
        return sql_result.one_or_none()


async def add_steam_skin_data(
        async_session: async_sessionmaker, weapon: str, skin: str, quality: str, stattrak: bool,
        offset: float, seed: int, price: float, link: str, param_a: str, param_m: str, param_s: str, param_d: str
):
    async with async_session() as session:
        weapon = await _select_obj_with_attrs(session, Weapon, 'weapon_name', weapon)
        skin = await _select_obj_with_attrs(session, Skin, 'skin_name', skin)
        quality = await _select_obj_with_attrs(session, Quality, 'quality_title', quality)
        stattrak = await _select_obj_with_attrs(session, StatTrak, 'stattrak_status', stattrak)

        stmt = insert(SteamSkinData).values(
            skin_id=skin.skin_id,
            weapon_id=weapon.weapon_id,
            quality_id=quality.quality_id,
            stattrak_id=stattrak.stattrak_id,
            offset=offset,
            seed=seed,
            price=price,
            link=link,
            param_a=param_a,
            param_m=param_m,
            param_s=param_s,
            param_d=param_d
        )
        await session.execute(stmt)
        await session.commit()




async def _select_obj_with_attrs(
        session: AsyncSession, class_obj: Callable, class_attribute, class_value,
) -> Row | None:
    stmt = select(class_obj).where(class_obj.__dict__[class_attribute] == class_value)
    result = await session.execute(stmt)
    item = result.scalar_one_or_none()
    return item


async def add_new_skin_to_db(
        async_session: async_sessionmaker,
        weapon_name: str, skin_name: str, stattrak_status: bool,
        *quality_data
) -> None:
    async with async_session() as session:
        skin = await _select_obj_with_attrs(session, Skin, 'skin_name', skin_name)
        if skin is None:
            skin = await session.scalar(
                insert(Skin).values(skin_name=skin_name).returning(Skin)
            )

        weapon = await _select_obj_with_attrs(session, Weapon, 'weapon_name', weapon_name)
        if weapon is None:
            weapon = await session.scalar(
                insert(Weapon).values(weapon_name=weapon_name).returning(Weapon)
            )
        skin_weapons = await skin.awaitable_attrs.weapons
        skin_weapons.append(weapon)

        stattrak = await _select_obj_with_attrs(
            session, StatTrak, 'stattrak_status', stattrak_status
        )
        if stattrak is None:
            stattrak = await session.scalar(
                insert(StatTrak).values(stattrak_status=stattrak_status).returning(StatTrak)
            )
        skin_stattraks = await skin.awaitable_attrs.stattraks
        skin_stattraks.append(stattrak)

        for item in quality_data:
            quality = await _select_obj_with_attrs(session, Quality, 'quality_title', item)
            if quality is None:
                quality = await session.scalar(
                    insert(Quality).values(quality_title=item).returning(Quality),
                )
            skin_qualities = await skin.awaitable_attrs.qualities
            skin_qualities.append(quality)

        await session.commit()


async def get_random_weapon_from_db(
        async_session: async_sessionmaker
) -> Row[Tuple[str, str, str, bool]] | None:
    async with async_session() as session:
        stmt = (
            select(Weapon.weapon_name, Skin.skin_name, Quality.quality_title, StatTrak.stattrak_status)
            .join(Skin.weapons)
            .join(Skin.qualities)
            .join(Skin.stattraks)
            .order_by(func.random())
            .limit(1)
        )
        result = await session.execute(stmt)
        return result.one_or_none()


async def get_all_skin_from_db(async_session: async_sessionmaker):
    async with async_session() as session:
        stmt = (
            select(Weapon.weapon_name, Skin.skin_name)
            .join(Skin.weapons)
        )
        result = await session.execute(stmt)
        return result.all()

