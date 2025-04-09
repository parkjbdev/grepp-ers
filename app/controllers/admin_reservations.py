from datetime import UTC, datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, status
from fastapi.encoders import jsonable_encoder
from starlette.responses import JSONResponse

from app.auth.auth_user import verify_admin
from app.controllers.user_reservations import ReservationWithSlotForResponse
from app.dependencies.config import admin_exam_management_service
from app.models.error_response_model import default_error_responses
from app.models.reservation_model import ReservationDto
from app.models.response_model import MessageResponseModel, MessageResponseWithResultModel
from app.models.user_model import User
from app.services.admin.admin_service_impl import AdminExamManagementService

router = APIRouter(prefix="/admin/reservations", tags=["관리자 예약관리"])

InjectService: AdminExamManagementService = Depends(admin_exam_management_service)


@router.get("",
            summary="회원들의 모든 예약 조회",
            description="회원들이 예약한 내역을 모두 조회합니다. ISO8601 포맷 작성시 TIME ZONE에 유의하세요!! TIME ZONE이 없으면 UTC로 간주합니다. ",
            status_code=status.HTTP_200_OK,
            responses=default_error_responses,
            response_model=MessageResponseWithResultModel[List[ReservationWithSlotForResponse]],
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
            raise ValueError("start_at must be before end_at")

    ret = await service.find_reservations(start_at, end_at)

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=jsonable_encoder(
            MessageResponseWithResultModel(
                message="예약 조회에 성공했습니다.",
                result=ret
            )
        )
    )


@router.patch("/{id}",
              summary="대기중인 예약 승인",
              description="예약 대기중인 내역을 승인합니다.",
              status_code=status.HTTP_200_OK,
              responses=default_error_responses,
              response_model=MessageResponseModel
              )
async def confirm_reservation(
        id: int,
        user: User = Depends(verify_admin),
        service=InjectService
):
    await service.confirm_reservation(id)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=jsonable_encoder(
            MessageResponseModel(
                message="예약 승인에 성공했습니다.",
            )
        )
    )


@router.put("/{id}",
            summary="예약 수정",
            description="예약을 수정합니다.",
            status_code=status.HTTP_200_OK,
            responses=default_error_responses,
            response_model=MessageResponseModel
            )
async def modify_reservation(
        id: int,
        reservation: ReservationDto,
        user: User = Depends(verify_admin),
        service=InjectService
):
    await service.modify_reservation(id, reservation)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=jsonable_encoder(
            MessageResponseModel(
                message="예약 수정에 성공했습니다.",
            )
        )
    )


@router.delete("/{id}",
               summary="예약 삭제",
               description="예약을 삭제합니다.",
               status_code=status.HTTP_200_OK,
               responses=default_error_responses,
               response_model=MessageResponseModel
               )
async def remove_reservation_by_id(
        id: int,
        user: User = Depends(verify_admin),
        service=InjectService
):
    await service.delete_reservation(id)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=jsonable_encoder(
            MessageResponseModel(
                message="예약 삭제에 성공했습니다.",
            )
        )
    )
