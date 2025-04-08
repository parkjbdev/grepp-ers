from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError

from app.auth.jwt import JWTUtils
from app.models.user_model import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token/form")


async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        return await JWTUtils.get_user_from_token(token)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def verify_admin(current_user: User = Depends(get_current_user)):
    if not current_user.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have sufficient permissions"
        )
    return current_user
