import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, status
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import ValidationError

from app.controllers.admin_reservations import router as admin_controller
from app.controllers.auth import router as auth_controller
from app.controllers.slot import router as slot_controller
from app.controllers.user_reservations import router as reservation_controller
from app.services.exceptions import DBConflictException, DBUnknownException, NotFoundException, UserNotFoundException

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.dependencies.config import database
    try:
        await database.connect()
    except Exception as e:
        print(e)
    yield
    await database.disconnect()


app = FastAPI(
    title="GREPP Exam Reservation System",
    summary=os.getenv("ENVIRONMENT"),
    description="Welcome to GREPP Exam Reservation System API Doc",
    root_path="/api",
    lifespan=lifespan
)

app.include_router(admin_controller)
app.include_router(auth_controller)
app.include_router(slot_controller)
app.include_router(reservation_controller)


@app.get("/",
         summary="API 문서",
         description="API 문서로 리다이렉트합니다.",
         )
async def root():
    return RedirectResponse(url="/docs")


@app.exception_handler(Exception)
async def exception_handler(request, exc):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error: " + str(exc)}
    )


@app.exception_handler(DBUnknownException)
async def db_unknown_exception_handler(request, exc):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Database error: " + str(exc)}
    )


@app.exception_handler(DBConflictException)
async def db_conflict_exception_handler(request, exc):
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": str(exc)}
    )


@app.exception_handler(NotFoundException)
async def db_unknown_exception_handler(request, exc):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": str(exc)}
    )


@app.exception_handler(UserNotFoundException)
async def user_not_found_exception_handler(request, exc):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": str(exc)}
    )


@app.exception_handler(ValueError)
async def value_error_exception_handler(request, exc):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc)}
    )
