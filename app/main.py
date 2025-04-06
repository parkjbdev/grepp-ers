from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, status
from fastapi.responses import JSONResponse, RedirectResponse

from app.controllers.admin_reservations import router as admin_controller
from app.controllers.auth import router as auth_controller
from app.controllers.slot import router as slot_controller
from app.controllers.user_reservations import router as reservation_controller


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_dotenv()
    from app.dependencies.config import database
    try:
        await database.connect()
    except Exception as e:
        print(e)
    yield
    await database.disconnect()


app = FastAPI(
    title="GREPP Exam Reservation System",
    description="Welcome to GREPP Exam Reservation System API Doc",
    root_path="/api",
    lifespan=lifespan
)

app.include_router(admin_controller)
app.include_router(auth_controller)
app.include_router(slot_controller)
app.include_router(reservation_controller)


@app.get("/",
         summary="Redoc API 문서",
         description="API 문서로 리다이렉트합니다.",
         status_code=301)
async def root():
    return RedirectResponse(url="/redoc", status_code=status.HTTP_301_MOVED_PERMANENTLY)


@app.exception_handler(Exception)
async def exception_handler(request, exc):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"}
    )
