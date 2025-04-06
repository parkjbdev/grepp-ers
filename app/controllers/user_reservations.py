from datetime import UTC, datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.auth.auth_user import get_current_user
from app.dependencies.config import exam_management_service
from app.models.reservation_model import Reservation
from app.models.user_model import User
from app.services.exam_management_service import ExamManagementService

router = APIRouter(prefix="/users/reservations", tags=["사용자 예약관리"])

InjectService: ExamManagementService = Depends(exam_management_service)


@router.get("",
            summary="자신의 예약 조회",
            description="자신이 예약한 내역을 조회합니다.",
            )
async def get_my_reservations(
        start_at: datetime = datetime.now(UTC),
        end_at: Optional[datetime] = datetime.now(UTC) + timedelta(days=30),
        user: User = Depends(get_current_user),
        service=InjectService
):
    return await service.find_reservations(user_id=user.id, start_at=start_at, end_at=end_at)


@router.get("/{id}",
            summary="자신의 예약 조회",
            description="자신이 예약한 내역을 ID로 조회합니다."
            )
async def get_reservation_by_id(
        id: int,
        user: User = Depends(get_current_user),
        service=InjectService
):
    return


class ReservationForm(BaseModel):
    slot_id: int
    amount: int


@router.post("",
             summary="새로운 예약 신청",
             description="새로운 예약을 신청합니다.")
async def submit_new_reservation(
        reservation: ReservationForm,
        user: User = Depends(get_current_user),
        service=InjectService
):
    res = Reservation(
        slot_id=reservation.slot_id,
        user_id=user.id,
        amount=reservation.amount
    )
    await service.add_reservation(res)
    return


@router.put("/{id}",
            summary="예약 수정",
            description="자신의 예약을 수정합니다. 예약이 확정되기 전에만 수정할 수 있습니다.")
async def modify_reservation(
        id: int,
        user: User = Depends(get_current_user),
        service=InjectService
):
    await service.delete_reservation(id, user.id)
    return


@router.delete("/{id}",
               summary="예약 삭제",
               description="자신의 예약을 삭제합니다. 예약이 확정되기 전에만 삭제할 수 있습니다.")
async def remove_reservation_by_id(
        id: int,
        user: User = Depends(get_current_user),
        service=InjectService
):
    await service.delete_reservation(id, user.id)
    return
