from typing import Callable, Dict, Any, Awaitable

from redis.asyncio import Redis
from aiogram import BaseMiddleware
from aiogram.types import Message


class GetterDefaultSettings(BaseMiddleware):
    def __init__(self, redis: Redis) -> None:
        super().__init__()
        self.redis = redis

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        redis_result = await self.redis.hgetall(f'{event.from_user.id}_settings')
        data['stattrak'] = True if redis_result[b'stattrak'].decode() == '1' else False
        data['quality'] = redis_result[b'quality'].decode()
        data['search'] = True if redis_result[b'search'].decode() == '1' else False
        return await handler(event, data)
