import datetime

from sqlalchemy import VARCHAR, Date, BigInteger
from sqlalchemy.orm import Mapped, mapped_column

from telegram_bot.db.base import Base


class User(Base):
    __tablename__ = 'user'

    # Telegram user_id
    user_id: Mapped[int] = mapped_column(
        BigInteger, unique=True, nullable=False, primary_key=True
    )
    # Telegram username
    username: Mapped[VARCHAR] = mapped_column(
        VARCHAR(32), unique=False, nullable=True
    )

    # Telegram user full name

    full_name: Mapped[VARCHAR] = mapped_column(
        VARCHAR(100), unique=False, nullable=True
    )

    # Registration date
    reg_date: Mapped[Date] = mapped_column(Date, default=datetime.date.today())

    # Last update date
    upd_date: Mapped[Date] = mapped_column(Date, onupdate=datetime.date.today(), nullable=True)

    def __repr__(self) -> str:
        return (f'{self.username}: '
                f'reg_day:{self.reg_date}; '
                f'upd_date{self.upd_date}; '
                f'id-{self.user_id} ')
