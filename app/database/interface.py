from abc import abstractmethod, ABC

from asyncpg import Pool


class Database(ABC):
    @abstractmethod
    async def connect(self): pass

    @abstractmethod
    async def disconnect(self): pass

    @abstractmethod
    def get_pool(self) -> Pool: pass
