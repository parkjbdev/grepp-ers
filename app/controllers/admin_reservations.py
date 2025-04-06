from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, status

from app.auth.auth_user import verify_admin
from app.models.reservation_model import Reservation
from app.models.user_model import User
from app.services.admin_exam_management_service import AdminExamManagementService

router = APIRouter(prefix="/admin/reservations", tags=["관리자 예약관리"])

InjectService: AdminExamManagementService = Depends(AdminExamManagementService)


@router.get("",
            summary="회원들의 모든 예약 조회",
            description="회원들이 예약한 내역을 모두 조회합니다.")
async def get_all_reservations(
        start_at: Optional[datetime] = None,
        end_at: Optional[datetime] = None,
        user: User = Depends(verify_admin),
        service=InjectService
):
    try:
        reservations = await service.find_reservations(start_at, end_at)
        return reservations
    except Exception as e:
        raise

    return


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
    except Exception as e:
        raise
    return


@router.put("/{id}",
            summary="예약 수정",
            description="예약을 수정합니다.")
async def modify_reservation(
        reservation: Reservation,
        user: User = Depends(verify_admin),
        service=InjectService
):
    try:
        await service.modify_reservation(reservation)
    except Exception as e:
        raise
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
    except Exception as e:
        raise
    return
