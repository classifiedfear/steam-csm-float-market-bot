from asyncio import Queue

from aiogram.fsm.state import StatesGroup, State


class ClosableQueue(Queue):
    SENTINEL = object

    async def close(self):
        await self.put(self.SENTINEL)

    async def __aiter__(self):
        while True:
            item = await self.get()
            try:
                if item is self.SENTINEL:
                    return
                yield item
            finally:
                self.task_done()


class SettingStates(StatesGroup):
    choosing_settings_state = State()
    choosing_stattrak_state = State()
    choosing_quality_state = State()
    choosing_search_state = State()
    canceling_state = State()


class OperationStates(StatesGroup):
    find_skin_by_msg_state = State()
    find_skin_by_db_state = State()
    add_new_skin_by_db = State()

