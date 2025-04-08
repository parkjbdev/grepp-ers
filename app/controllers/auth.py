from argon2.exceptions import VerifyMismatchError
from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel
from starlette.responses import JSONResponse

from app.auth.jwt import JWTUtils
from app.dependencies.config import auth_service
from app.models.response_model import MessageResponseModel
from app.models.user_model import User
from app.services.auth.auth_service_impl import AuthService, UserNotFoundException

router = APIRouter(
    prefix="/auth",
    tags=["인증"],
)

InjectAuthService: AuthService = Depends(auth_service)


class UserForm(BaseModel):
    username: str
    password: str


@router.post("/register",
             summary="회원가입",
             description="회원가입을 진행합니다.",
             status_code=status.HTTP_201_CREATED,
             response_model=MessageResponseModel
             )
async def register_user(user: UserForm, service=InjectAuthService):
    user = User(**user.model_dump())
    await service.add_user(User(**user.model_dump(include={"username", "password"})))
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content=MessageResponseModel(
            message=f"User {user.username} registered successfully",
        )
    )


@router.post("/token",
             summary="로그인 토큰 발급",
             description="로그인 후 토큰을 발급받습니다. 토큰은 Bearer 방식으로 헤더에 담아 사용합니다.",
             status_code=status.HTTP_200_OK,
             response_model=MessageResponseModel
             )
async def login_user(user: UserForm, response: Response, service=InjectAuthService):
    try:
        user = await service.authenticate_user(user.username, user.password)
        access_token = JWTUtils.issue_access_token(user)
        response.headers["Authorization"] = f"Bearer {access_token}"

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
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=MessageResponseModel(
            message="Login successful",
        )
    )
