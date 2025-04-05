from abc import ABC, abstractmethod


class UserRepository(ABC):
    @abstractmethod
    async def find(self, username: str): pass

    @abstractmethod
    async def insert(self, username: str, password: str): pass

    @abstractmethod
    async def delete_by_username(self, username: str): pass

    @abstractmethod
    async def delete(self, userid: int): pass

    @abstractmethod
    async def update_password(self, username: str, password: str): pass
