from telegram_bot.abc.handlers import CompositeHandler


class GeneralHandler(CompositeHandler):
    def __init__(self):
        self._handlers = set()
