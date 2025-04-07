from abc import ABC, abstractmethod

from app.models.user_model import User


class AuthService(ABC):

    @abstractmethod
    async def add_user(self, user: User): pass

    @abstractmethod
    async def authenticate_user(self, username: str, password: str): pass

    @abstractmethod
    async def reset_password(self, username: str, password: str): pass

    @abstractmethod
    async def delete_user(self, username: str): pass
