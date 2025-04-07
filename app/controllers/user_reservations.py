from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from starlette import status

from app.auth.auth_user import get_current_user
from app.dependencies.config import exam_management_service
from app.models.reservation_model import Reservation, ReservationDto
from app.models.user_model import User
from app.repositories.reservation.exceptions import SlotLimitExceededException
from app.services.user.user_service_impl import ExamManagementService

router = APIRouter(prefix="/users/reservations", tags=["사용자 예약관리"])

InjectService: ExamManagementService = Depends(exam_management_service)


@router.get("",
            summary="자신의 예약 조회",
            description="자신이 예약한 내역을 조회합니다.",
            )
async def get_my_reservations(
        start_at: Optional[datetime] = None,
        end_at: Optional[datetime] = None,
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
    return await service.find_reservation_by_id(id)


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
    try:
        await service.add_reservation(res)
    except SlotLimitExceededException as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Slot limit exceeded: The slot limit 50000 exceeded"
        )
    return


@router.put("/{id}",
            summary="예약 수정",
            description="자신의 예약을 수정합니다. 예약이 확정되기 전에만 수정할 수 있습니다.")
async def modify_reservation(
        id: int,
        reservation: ReservationDto,
        user: User = Depends(get_current_user),
        service=InjectService
):
    try:
        await service.modify_reservation(id, reservation, user.id)
    except SlotLimitExceededException as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Slot limit exceeded: The slot limit 50000 exceeded"
        )
    except KeyError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reservation not found: {id}"
        )
    return


@router.delete("/{id}",
               summary="예약 삭제",
               description="자신의 예약을 삭제합니다. 예약이 확정되기 전에만 삭제할 수 있습니다.")
async def remove_reservation_by_id(
        id: int,
        user: User = Depends(get_current_user),
        service=InjectService
):
    try:
        await service.delete_reservation(id, user.id)
    except KeyError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reservation not found: {id}"
        )
    return
