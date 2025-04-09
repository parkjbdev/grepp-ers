from abc import ABC, abstractmethod


class UserRepository(ABC):
    @abstractmethod
    async def find(self, username: str): pass

    @abstractmethod
    async def insert(self, username: str, hashed_password: str): pass

    @abstractmethod
    async def delete(self, username: str): pass

    @abstractmethod
    async def update_password(self, username: str, hashed_password: str): pass
