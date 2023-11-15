from typing import Any, Dict, Callable, Awaitable

from aiogram import BaseMiddleware
from redis.asyncio import Redis
from aiogram.types import Message


class SettingsCheck(BaseMiddleware):
    def __init__(self, redis: Redis) -> None:
        super().__init__()
        self.redis = redis

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        #await self.redis.delete(f'{event.from_user.id}_settings')
        if redis_result := await self.redis.hgetall(f'{event.from_user.id}_settings'):
            data['stattrak'] = True if redis_result[b'stattrak'].decode() == '1' else False
            data['quality'] = redis_result[b'quality'].decode()
            data['search'] = True if redis_result[b'search'].decode() == '1' else False
            return await handler(event, data)

        quality_settings, stattrak_setting, search_setting = 'Field-Tested', False, False

        await self.redis.hset(f'{event.from_user.id}_settings', mapping={
            'stattrak': '0',
            'search': '0',
            'quality': quality_settings,
        })

        data['stattrak'] = stattrak_setting
        data['quality'] = quality_settings
        data['search'] = search_setting

        return await handler(event, data)
