import os
from datetime import UTC, datetime, timedelta
from typing import Optional

from fastapi import HTTPException, status
from jose import JWTError, jwt

from app.models.user_model import User


class JWTUtils:
    # JWT
    @staticmethod
    def issue_access_token(user: User, expires_delta: Optional[timedelta] = timedelta(minutes=30)):
        to_encode = user.model_dump(include={"username", "admin"}).copy()
        expire = datetime.now(UTC) + expires_delta
        to_encode.update({
            "sub": user.username,
            "exp": expire,
            "iat": datetime.now(UTC)
        })
        return jwt.encode(to_encode, os.getenv("JWT_SECRET"), algorithm="HS256")

    @staticmethod
    async def get_user_from_token(token: str):
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = jwt.decode(token, os.getenv("JWT_SECRET"), algorithms="HS256")
            username: str = payload.get("username")
            admin: bool = payload.get("admin", False)
            if username is None:
                raise credentials_exception
        except JWTError:
            raise credentials_exception

        return User(username=username, admin=admin)
