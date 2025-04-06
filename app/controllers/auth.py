import os

from argon2.exceptions import VerifyMismatchError
from asyncpg import UniqueViolationError
from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.auth.jwt import JWTUtils
from app.dependencies.config import auth_service
from app.models.user_model import User
from app.services.auth_service import AuthService, UserNotFoundException

router = APIRouter(
    prefix="/auth",
)

InjectAuthService: AuthService = Depends(auth_service)


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_user(user: User, service=InjectAuthService):
    user = User(**user.model_dump(include={"username", "password"}))
    try:
        await service.add_user(User(**user.model_dump(include={"username", "password"})))
    except UniqueViolationError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already exists",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )
    return


@router.post("/token", status_code=status.HTTP_200_OK)
async def login_user(user: User, response: Response, service=InjectAuthService):
    try:
        user = await service.authenticate_user(user.username, user.password)
        print(user)
        access_token = JWTUtils.issue_access_token(user)
        response.headers["Authorization"] = f"Bearer {access_token}"
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=True if os.getenv("ENVIRONMENT") == "PRODUCTION" else False,
            samesite="lax",
            max_age=int(os.getenv("JWT_EXPIRES_SEC")),
        )

    except VerifyMismatchError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    except UserNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {e.username} not found",
        )
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )

    return user.model_dump(include={"username", "admin"})
