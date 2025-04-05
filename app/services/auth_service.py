import asyncio
from abc import ABC, abstractmethod

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from app.models.user_model import User
from app.repositories.user.dbimpl import UserRepository


class AuthService(ABC):

    @abstractmethod
    async def add_user(self, user: User): pass

    @abstractmethod
    async def authenticate_user(self, username: str, password: str): pass

    @abstractmethod
    async def reset_password(self, username: str, password: str): pass

    @abstractmethod
    async def delete_user(self, userid: int): pass


class UserNotFoundException(Exception):
    def __init__(self, username: str):
        self.username = username
        self.message = f"사용자 ID {username}를 찾을 수 없습니다"
        super().__init__(self.message)


class AuthServiceImpl(AuthService):
    def __init__(self, repo: UserRepository):
        self.repo = repo
        self.ph = PasswordHasher()

    # Non-Login State
    async def add_user(self, user: User):
        hashed_password = self.ph.hash(user.password)
        await self.repo.insert(user.username, hashed_password)

    async def authenticate_user(self, username: str, password: str):
        user = await self.repo.find(username)
        if user is None:
            raise UserNotFoundException(username)

        try:
            self.ph.verify(user.password, password)
            if self.ph.check_needs_rehash(user.password):
                new_pass = self.ph.hash(password)
                # await self.repo.update_password(username, new_pass)
                # 실패해도 큰 문제 없음.. 비동기
                asyncio.create_task(self.repo.update_password(username, new_pass))

            return user

        except VerifyMismatchError as e:
            raise

    # Login State
    async def reset_password(self, username: str, password: str):
        hashed_password = self.ph.hash(password)
        await self.repo.update_password(username, hashed_password)

    async def delete_user(self, userid: int):
        await self.repo.delete(userid)
