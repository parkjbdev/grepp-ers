from __future__ import annotations

from app.database.ers_db import ExamReservationSystemDatabase
from app.database.interface import Database

# To Prevent Circular Import Problem
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.repositories.reservation.dbimpl import ReservationRepository
    from app.repositories.slot.dbimpl import SlotRepository
    from app.repositories.user.dbimpl import UserRepository
    from app.services.auth_service import AuthService
    from app.services.exam_management_service import ExamManagementService


# database
def database() -> Database:
    return ExamReservationSystemDatabase()


# repositories
def reservation_repository() -> ReservationRepository:
    from app.repositories.reservation.dbimpl import ReservationRepositoryImpl
    return ReservationRepositoryImpl()


def slot_repository() -> SlotRepository:
    from app.repositories.slot.dbimpl import SlotRepositoryImpl
    return SlotRepositoryImpl()


def user_repository() -> UserRepository:
    from app.repositories.user.dbimpl import UserRepositoryImpl
    return UserRepositoryImpl()


# services
def auth_service() -> AuthService:
    from app.services.auth_service import AuthServiceImpl
    return AuthServiceImpl()


def reservation_service() -> ExamManagementService:
    from app.services.exam_management_service import ExamManagementServiceImpl
    return ExamManagementServiceImpl()
