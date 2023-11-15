from __future__ import annotations

from typing import List

from sqlalchemy import (
    Column,                     
    Integer,
    String,
    ForeignKey, 
    Table, 
    Boolean,
    Float,
    BigInteger
    )

from sqlalchemy.orm import (
    relationship,
    Mapped,
    mapped_column
    )


from .base import Base
from telegram_bot.resources import db_const as db_const


quality_skin: Table = Table(
    db_const.quality_skin_table,
    Base.metadata,
    Column('quality_id', Integer, ForeignKey("qualities.quality_id")),
    Column('skin_id', Integer, ForeignKey("skins.skin_id"))
    )

weapon_skin: Table = Table(
    db_const.skin_weapon_table,
    Base.metadata,
    Column('weapon_id', Integer, ForeignKey('weapons.weapon_id')),
    Column('skin_id', Integer, ForeignKey('skins.skin_id'))
)

stattrak_skin: Table = Table(
    db_const.stattrak_skin,
    Base.metadata, 
    Column('stattrak_id', Integer, ForeignKey('stattraks.stattrak_id')),
    Column('skin_id', Integer, ForeignKey('skins.skin_id'))
)


class Weapon(Base):
    __tablename__ = 'weapons'

    weapon_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, unique=True)

    weapon_name: Mapped[str] = mapped_column(String, unique=True, nullable=False)

    skins: Mapped[List[Skin]] = relationship(
        'Skin', secondary=weapon_skin, back_populates='weapons'
    )


class Skin(Base):
    __tablename__ = 'skins'

    skin_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, unique=True)

    skin_name: Mapped[str] = mapped_column(String, unique=True, nullable=False)

    qualities: Mapped[List[Quality]] = relationship(
        'Quality', secondary=quality_skin, back_populates='skins'
    )

    weapons: Mapped[List[Weapon]] = relationship(
        'Weapon', secondary=weapon_skin, back_populates='skins'
    )

    stattraks: Mapped[List[StatTrak]] = relationship(
        'StatTrak', secondary=stattrak_skin, back_populates='skins'
    )


class SteamSkinData(Base):
    __tablename__ = 'steam_skins_data'

    skin_data_id: Mapped[int] = mapped_column(Integer, primary_key=True, unique=True, nullable=False)

    skin_id: Mapped[int] = Column(Integer, ForeignKey('skins.skin_id'))

    weapon_id: Mapped[int] = Column(Integer, ForeignKey('weapons.weapon_id'))

    quality_id: Mapped[int] = Column(Integer, ForeignKey('qualities.quality_id'))

    stattrak_id: Mapped[int] = Column(Integer, ForeignKey('stattraks.stattrak_id'))

    offset: Mapped[float] = mapped_column(Float, unique=True, nullable=False)

    seed: Mapped[int] = mapped_column(Integer, nullable=False)

    price: Mapped[float] = mapped_column(Float, nullable=False)

    link: Mapped[str] = mapped_column(String, unique=True, nullable=False)

    param_a: Mapped[int] = mapped_column(String, unique=True, nullable=False)

    param_m: Mapped[int] = mapped_column(String, nullable=True)

    param_s: Mapped[int] = mapped_column(String, nullable=True)

    param_d: Mapped[int] = mapped_column(String, unique=True, nullable=False)


class Quality(Base):
    __tablename__ = 'qualities'

    quality_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, unique=True)

    quality_title: Mapped[str] = mapped_column(String, unique=True, nullable=False)

    skins: Mapped[List[Skin]] = relationship(
        'Skin', secondary=quality_skin, back_populates='qualities'
    )


class StatTrak(Base):
    __tablename__ = 'stattraks'

    stattrak_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, unique=True)

    stattrak_status: Mapped[bool] = mapped_column(Boolean, unique=True, nullable=False)

    skins: Mapped[List[Skin]] = relationship(
        'Skin', secondary=stattrak_skin, back_populates='stattraks'
    )
