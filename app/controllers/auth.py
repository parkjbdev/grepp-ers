from fastapi import APIRouter

router = APIRouter(prefix="/auth")


@router.post("/register")
async def register_user():
    return


@router.post("/login")
async def login_user():
    return


@router.post("/logout")
async def logout_user():
    return
