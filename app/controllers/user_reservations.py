from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends

from app.auth.auth_user import get_current_user
from app.models.user_model import User
from app.services.exam_management_service import ExamManagementService, ExamManagementServiceImpl

router = APIRouter(prefix="/users/reservations", tags=["사용자 예약관리"])

InjectService: ExamManagementService = Depends(ExamManagementServiceImpl)


@router.get("",
            summary="자신의 예약 조회",
            description="자신이 예약한 내역을 조회합니다.")
async def get_my_reservations(
        start_at: int = datetime.now(),
        end_at: Optional[int] = None,
        user: User = Depends(get_current_user),
        service=InjectService
):
    return


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


@router.post("",
             summary="새로운 예약 신청",
             description="새로운 예약을 신청합니다.")
async def submit_new_reservation(
        user: User = Depends(get_current_user),
        service=InjectService
):
    return


@router.put("/{id}",
            summary="예약 수정",
            description="자신의 예약을 수정합니다. 예약이 확정되기 전에만 수정할 수 있습니다.")
async def modify_reservation(
        id: int,
        user: User = Depends(get_current_user),
        service=InjectService
):
    return


@router.delete("/{id}",
               summary="예약 삭제",
               description="자신의 예약을 삭제합니다. 예약이 확정되기 전에만 삭제할 수 있습니다.")
async def remove_reservation_by_id(
        id: int,
        user: User = Depends(get_current_user),
        service=InjectService
):
    return
