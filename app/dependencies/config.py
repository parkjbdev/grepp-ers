from __future__ import annotations

# To Prevent Circular Import Problem
from typing import Annotated, TYPE_CHECKING

from asyncpg import Pool
from fastapi import Depends

from app.database import ers_db

if TYPE_CHECKING:
    from app.repositories.reservation.dbimpl import ReservationRepository
    from app.repositories.slot.dbimpl import SlotRepository
    from app.repositories.user.dbimpl import UserRepository
    from app.services.auth.auth_service_impl import AuthService
    from app.services.user.user_service_impl import ExamManagementService
    from app.services.admin.admin_service_impl import AdminExamManagementService

# database
database = ers_db


# repositories
def user_repository(pool: Annotated[Pool, Depends(database.get_pool)]) -> UserRepository:
    from app.repositories.user.dbimpl import UserRepositoryImpl
    return UserRepositoryImpl(pool)


def slot_repository(pool: Annotated[Pool, Depends(database.get_pool)]) -> SlotRepository:
    from app.repositories.slot.dbimpl import SlotRepositoryImpl
    return SlotRepositoryImpl(pool)


def reservation_repository(pool: Annotated[Pool, Depends(database.get_pool)]) -> ReservationRepository:
    from app.repositories.reservation.dbimpl import ReservationRepositoryImpl
    return ReservationRepositoryImpl(pool)


# services
def auth_service(user_repo=Depends(user_repository)) -> AuthService:
    from app.services.auth.auth_service_impl import AuthServiceImpl
    return AuthServiceImpl(user_repo)


def exam_management_service(slot_repo=Depends(slot_repository),
                            reservation_repo=Depends(reservation_repository)) -> ExamManagementService:
    from app.services.user.user_service_impl import ExamManagementServiceImpl
    return ExamManagementServiceImpl(slot_repo=slot_repo, reservation_repo=reservation_repo)


def admin_exam_management_service(slot_repo=Depends(slot_repository),
                                  reservation_repo=Depends(reservation_repository)) -> AdminExamManagementService:
    from app.services.admin.admin_service_impl import AdminExamManagementServiceImpl
    return AdminExamManagementServiceImpl(slot_repo=slot_repo, reservation_repo=reservation_repo)
