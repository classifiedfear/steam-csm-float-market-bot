from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import Message
from redis import asyncio as aioredis


from telegram_bot.db.base import get_session_maker, ENGINE
from telegram_bot.db import db_query


class RegisterCheck(BaseMiddleware):
    def __init__(self,redis: aioredis) -> None:
        super().__init__()
        self.redis = redis

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        #await self.redis.delete(str(event.from_user.id))
        if await self.redis.get(name=str(event.from_user.id)):
            return await handler(event, data)
        if not await db_query.is_user_exists(
                get_session_maker(ENGINE), event.from_user.id
        ):
            await db_query.add_user(
                get_session_maker(ENGINE),
                event.from_user.id,
                event.from_user.username,
                event.from_user.full_name
            )
            await self.redis.set(name=str(event.from_user.id), value=1)
        return await handler(event, data)
