from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends
from fastapi.encoders import jsonable_encoder
from starlette import status
from starlette.responses import JSONResponse

from app.auth.auth_user import get_current_user
from app.dependencies.config import exam_management_service
from app.models.reservation_model import Reservation, ReservationDto
from app.models.response_model import MessageResponseModel, MessageResponseWithResultModel
from app.models.slot_model import TimeRangeSchema
from app.models.slot_reservation_joined_model import ReservationWithSlot
from app.models.user_model import User
from app.services.user.user_service_impl import ExamManagementService

router = APIRouter(prefix="/users/reservations", tags=["사용자 예약관리"])

InjectService: ExamManagementService = Depends(exam_management_service)


class ReservationWithSlotForResponse(ReservationWithSlot):
    time_range: TimeRangeSchema


@router.get("",
            summary="자신의 예약 조회",
            description="자신이 예약한 내역을 조회합니다.",
            status_code=status.HTTP_200_OK,
            response_model=MessageResponseWithResultModel[List[ReservationWithSlotForResponse]]
            )
async def get_my_reservations(
        start_at: Optional[datetime] = None,
        end_at: Optional[datetime] = None,
        user: User = Depends(get_current_user),
        service=InjectService
):
    ret = await service.find_reservations(user_id=user.id, start_at=start_at, end_at=end_at)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=jsonable_encoder(
            MessageResponseWithResultModel[List[ReservationWithSlotForResponse]](
                message="예약 조회에 성공했습니다.",
                result=ret
            )
        )
    )


@router.get("/{id}",
            summary="자신의 예약 조회",
            description="자신이 예약한 내역을 ID로 조회합니다.",
            status_code=status.HTTP_200_OK,
            response_model=MessageResponseWithResultModel[ReservationWithSlotForResponse]
            )
async def get_reservation_by_id(
        id: int,
        user: User = Depends(get_current_user),
        service=InjectService
):
    ret = await service.find_reservation_by_id(id)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=jsonable_encoder(
            MessageResponseWithResultModel(
                message="예약 조회에 성공했습니다.",
                result=ret
            )
        )
    )


@router.post("",
             summary="새로운 예약 신청",
             description="새로운 예약을 신청합니다.",
             status_code=status.HTTP_201_CREATED,
             response_model=MessageResponseModel
             )
async def submit_new_reservation(
        reservation: ReservationDto,
        user: User = Depends(get_current_user),
        service=InjectService
):
    res = Reservation(
        slot_id=reservation.slot_id,
        user_id=user.id,
        amount=reservation.amount
    )
    await service.add_reservation(res)
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content=jsonable_encoder(
            MessageResponseModel(message="예약이 완료되었습니다."),
        )
    )


@router.put("/{id}",
            summary="예약 수정",
            description="자신의 예약을 수정합니다. 예약이 확정되기 전에만 수정할 수 있습니다.",
            status_code=status.HTTP_200_OK,
            response_model=MessageResponseModel
            )
async def modify_reservation(
        id: int,
        reservation: ReservationDto,
        user: User = Depends(get_current_user),
        service=InjectService
):
    await service.modify_reservation(id, reservation, user.id)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=jsonable_encoder(
            MessageResponseModel(message="예약이 수정되었습니다."),
        )
    )


@router.delete("/{id}",
               summary="예약 삭제",
               description="자신의 예약을 삭제합니다. 예약이 확정되기 전에만 삭제할 수 있습니다.",
               status_code=status.HTTP_200_OK,
               response_model=MessageResponseModel
               )
async def remove_reservation_by_id(
        id: int,
        user: User = Depends(get_current_user),
        service=InjectService
):
    await service.delete_reservation(id, user.id)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=jsonable_encoder(
            MessageResponseModel(message="예약이 삭제되었습니다."),
        )
    )
