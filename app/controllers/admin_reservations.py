from datetime import datetime
from typing import Optional

from fastapi import APIRouter

router = APIRouter(prefix="/admin/reservations", tags=["관리자 예약관리"])


@router.get("",
            summary="회원들의 모든 예약 조회",
            description="회원들이 예약한 내역을 모두 조회합니다.")
async def get_all_reservations(start_at: int = datetime.now(), end_at: Optional[int] = None):
    return


@router.patch("/{id}",
              summary="대기중인 예약 승인",
              description="예약 대기중인 내역을 승인합니다.")
async def confirm_reservation(id: int):
    return


@router.put("/{id}",
            summary="예약 수정",
            description="예약을 수정합니다.")
async def modify_reservation(id: int):
    return


@router.delete("/{id}",
               summary="예약 삭제",
               description="예약을 삭제합니다.")
async def remove_reservation_by_id(id: int):
    return
