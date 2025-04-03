from contextlib import asynccontextmanager

from fastapi import FastAPI
from dotenv import load_dotenv
from starlette import status
from starlette.responses import RedirectResponse

from app.controllers.user_reservations import router as reservation_controller
from app.controllers.admin_reservations import router as admin_controller
from app.controllers.slot import router as slot_controller
from app.controllers.auth import router as auth_controller
from app.dependencies.config import get_database

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await get_database().connect()
    yield
    await get_database().disconnect()


app = FastAPI(
    title="GREPP Exam Reservation System",
    description="Welcome to GREPP Exam Reservation System API Doc",
    root_path="/api",
    lifespan=lifespan
)

app.include_router(reservation_controller)
app.include_router(admin_controller)
app.include_router(slot_controller)
app.include_router(auth_controller)


@app.get("/",
         summary="Redoc API 문서",
         description="API 문서로 리다이렉트합니다.",
         status_code=301)
async def root():
    return RedirectResponse(url="/redoc", status_code=status.HTTP_301_MOVED_PERMANENTLY)
