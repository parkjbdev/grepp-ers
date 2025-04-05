import functools

from asyncpg import RaiseError


class SlotLimitExceededException(Exception):
    def __init__(self, message="The maximum number of slots for this time period has been exceeded"):
        self.message = message
        super().__init__(self.message)

