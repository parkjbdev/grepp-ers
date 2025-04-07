from datetime import UTC, datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.auth_user import verify_admin
from app.dependencies.config import admin_exam_management_service
from app.models.reservation_model import ReservationDto
from app.models.user_model import User
from app.repositories.reservation.exceptions import SlotLimitExceededException
from app.services.admin.admin_service_impl import AdminExamManagementService

router = APIRouter(prefix="/admin/reservations", tags=["관리자 예약관리"])

InjectService: AdminExamManagementService = Depends(admin_exam_management_service)


@router.get("",
            summary="회원들의 모든 예약 조회",
            description="회원들이 예약한 내역을 모두 조회합니다.",
            status_code=status.HTTP_200_OK
            )
async def get_all_reservations(
        start_at: Optional[datetime] = None,
        end_at: Optional[datetime] = None,
        user: User = Depends(verify_admin),
        service=InjectService
):
    if start_at and start_at is not None:
        if start_at.tzinfo is None:
            start_at = start_at.replace(tzinfo=UTC)
    if end_at and end_at is not None:
        if end_at.tzinfo is None:
            end_at = end_at.replace(tzinfo=UTC)

    if start_at is not None and end_at is not None:
        if start_at > end_at:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="start_at must be before end_at",
            )

    return await service.find_reservations(start_at, end_at)


@router.patch("/{id}",
              summary="대기중인 예약 승인",
              description="예약 대기중인 내역을 승인합니다.",
              status_code=status.HTTP_200_OK
              )
async def confirm_reservation(
        id: int,
        user: User = Depends(verify_admin),
        service=InjectService
):
    try:
        await service.confirm_reservation(id)
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


@router.put("/{id}",
            summary="예약 수정",
            description="예약을 수정합니다.",
            status_code=status.HTTP_200_OK
            )
async def modify_reservation(
        id: int,
        reservation: ReservationDto,
        user: User = Depends(verify_admin),
        service=InjectService
):
    try:
        await service.modify_reservation(id, reservation)
    except SlotLimitExceededException as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Slot limit exceeded: The slot limit 50000 exceeded"
        )
    except KeyError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reservation not found: {reservation.id}"
        )
    return


@router.delete("/{id}",
               summary="예약 삭제",
               description="예약을 삭제합니다.")
async def remove_reservation_by_id(
        id: int,
        user: User = Depends(verify_admin),
        service=InjectService
):
    try:
        await service.delete_reservation(id)
    except KeyError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Reservation not found: {id}"
                            )
    return
