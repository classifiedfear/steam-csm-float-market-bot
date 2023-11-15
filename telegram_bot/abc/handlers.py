from abc import abstractmethod, ABC
from typing import List, Self

from aiogram import Router


class Handler(ABC):
    _router = None

    @property
    def is_composite(self):
        return False

    @property
    def router(self):
        return self._router

    @abstractmethod
    async def execute(self) -> None:
        pass


class CompositeHandler(Handler):
    _handlers = None

    @property
    def is_composite(self):
        return True

    def add(self, handler: Handler) -> Self:
        self._handlers.add(handler)
        return self

    def remove(self, handler: Handler) -> Self:
        self._handlers.remove(handler)
        return self

    async def execute(self) -> None:
        for handler in self._handlers:
            await handler.execute()

    @property
    def router(self) -> List[Router]:
        routers = []
        if self._router is not None:
            routers.append(self._router)
        for handler in self._handlers:
            if handler.is_composite:
                for router in handler.router:
                    routers.append(router)
            else:
                routers.append(handler.router)
        return routers
