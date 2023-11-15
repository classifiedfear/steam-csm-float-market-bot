import abc


class BotCommand(abc.ABC):

    @abc.abstractmethod
    async def execute(self):
        pass