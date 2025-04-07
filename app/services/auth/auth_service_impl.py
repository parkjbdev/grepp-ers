import asyncio
from abc import ABC, abstractmethod

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from asyncpg import PostgresError

from app.models.user_model import User
from app.repositories.user.dbimpl import UserRepository
from app.repositories.user.exceptions import NoSuchUserException, UserNameAlreadyExistsException
from app.services.auth.interface import AuthService
from app.services.exceptions import DBConflictException, DBUnknownException, UserNotFoundException


class AuthServiceImpl(AuthService):
    def __init__(self, repo: UserRepository):
        self.repo = repo
        self.ph = PasswordHasher()

    # Non-Login State
    async def add_user(self, user: User):
        hashed_password = self.ph.hash(user.password)
        try:
            ret = await self.repo.insert(user.username, hashed_password)
            if ret is None:
                raise DBUnknownException()
        except UserNameAlreadyExistsException as e:
            raise DBConflictException(str(e))
        except PostgresError as e:
            raise DBUnknownException()

    async def authenticate_user(self, username: str, password: str):
        try:
            user = await self.repo.find(username)
        except NoSuchUserException as e:
            raise UserNotFoundException(username)
        except PostgresError as e:
            raise DBUnknownException()

        user = User(**dict(user))

        try:
            self.ph.verify(user.password, password)
            if self.ph.check_needs_rehash(user.password):
                new_pass = self.ph.hash(password)
                # 실패해도 큰 문제 없음.. 비동기
                # await self.repo.update_password(username, new_pass)
                # 이렇게 하면.. 실행 task로 던져놓고 계속 진행
                asyncio.create_task(self.repo.update_password(username, new_pass))

            return user
        except VerifyMismatchError as e:
            raise

    # Login State
    async def reset_password(self, username: str, password: str):
        hashed_password = self.ph.hash(password)
        try:
            await self.repo.update_password(username, hashed_password)
        except NoSuchUserException as e:
            raise UserNotFoundException(username)
        except PostgresError as e:
            raise DBUnknownException()

    async def delete_user(self, username: str):
        try:
            await self.repo.delete(username)
        except NoSuchUserException as e:
            raise UserNotFoundException(username)
        except PostgresError as e:
            raise DBUnknownException()
