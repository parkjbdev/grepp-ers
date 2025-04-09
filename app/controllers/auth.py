from argon2.exceptions import VerifyMismatchError
from fastapi import APIRouter, Depends, Form, HTTPException, Response, status
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from starlette.responses import JSONResponse

from app.auth.jwt import JWTUtils
from app.dependencies.config import auth_service
from app.models.error_response_model import default_error_responses
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
             responses=default_error_responses,
             response_model=MessageResponseModel
             )
async def register_user(user: UserForm, service=InjectAuthService):
    user = User(**user.model_dump())
    await service.add_user(User(**user.model_dump(include={"username", "password"})))
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content=jsonable_encoder(
            MessageResponseModel(
                message=f"User {user.username} registered successfully",
            )
        )
    )


async def handle_login(username: str, password: str, service=InjectAuthService):
    try:
        user = await service.authenticate_user(username, password)
        access_token = JWTUtils.issue_access_token(user)
        return access_token

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


@router.post("/token",
             summary="로그인 토큰 발급",
             description="로그인 후 토큰을 발급받습니다. 토큰은 Bearer 방식으로 헤더에 담아 사용합니다.",
             status_code=status.HTTP_200_OK,
             responses=default_error_responses,
             response_model=MessageResponseModel
             )
async def login_user(user: UserForm, response: Response, service=InjectAuthService):
    access_token = await handle_login(user.username, user.password, service)
    response.headers["Authorization"] = f"Bearer {access_token}"
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=jsonable_encoder(
            MessageResponseModel(
                message="Login successful",
            )
        )
    )


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/token/form",
             summary="로그인 토큰 발급",
             description="로그인 후 토큰을 발급받습니다. 토큰은 Bearer 방식으로 헤더에 담아 사용합니다. Swagger UI에서 사용하기 위해 x-www-form-urlencoded로 작성한 엔드포인트입니다.",
             status_code=status.HTTP_200_OK,
             responses=default_error_responses,
             response_model=TokenResponse
             )
async def login_user_from_form(
        response: Response,
        username: str = Form(...),
        password: str = Form(...),
        service=InjectAuthService):
    access_token = await handle_login(username, password, service)
    response.headers["Authorization"] = f"Bearer {access_token}"
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=jsonable_encoder(
            TokenResponse(
                access_token=access_token,
                token_type="bearer",
            )
        )
    )
