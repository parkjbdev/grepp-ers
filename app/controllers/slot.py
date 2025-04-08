from datetime import UTC, datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from starlette.responses import JSONResponse

from app.auth.auth_user import verify_admin
from app.dependencies.config import admin_exam_management_service, exam_management_service
from app.models.response_model import MessageResponseModel, MessageResponseWithResultModel
from app.models.slot_model import Slot, SlotForResponse
from app.models.user_model import User
from app.services.admin.admin_service_impl import AdminExamManagementService
from app.services.user.user_service_impl import ExamManagementService

router = APIRouter(prefix="/slots", tags=["테스트 슬롯"])

InjectService: ExamManagementService = Depends(exam_management_service)
InjectAdminService: AdminExamManagementService = Depends(admin_exam_management_service)


@router.get("",
            summary="슬롯 조회",
            description="슬롯을 조회합니다.",
            status_code=status.HTTP_200_OK,
            response_model=MessageResponseWithResultModel[List[SlotForResponse]]
            )
async def get_available_slots(
        start_at: Optional[datetime] = None,
        end_at: Optional[datetime] = None,
        service=InjectService
):
    try:
        if start_at and start_at.tzinfo is None:
            start_at = start_at.replace(tzinfo=timezone.utc)
        if end_at and end_at.tzinfo is None:
            end_at = end_at.replace(tzinfo=timezone.utc)

        if start_at is not None and end_at is not None:
            if start_at > end_at:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="start_at must be before end_at",
                )
        rows = await service.find_slots(start_at, end_at)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=jsonable_encoder(
                MessageResponseWithResultModel[List[SlotForResponse]](
                    message="슬롯 조회에 성공했습니다.",
                    result=list(map(lambda x: SlotForResponse.from_slot_with_amount(x), rows))
                )
            )
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date format",
        )


@router.get("/{id}",
            summary="슬롯 조회",
            description="슬롯을 ID로 조회합니다.",
            status_code=status.HTTP_200_OK,
            response_model=MessageResponseWithResultModel[SlotForResponse]
            )
async def get_slot_by_id(
        id: int,
        service=InjectService
):
    slot = await service.find_slot_by_id(id)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=jsonable_encoder(
            MessageResponseWithResultModel[SlotForResponse](
                message="슬롯 조회에 성공했습니다.",
                result=SlotForResponse.from_slot_with_amount(slot)
            )
        )
    )


class SlotForm(BaseModel):
    start_at: datetime
    end_at: datetime


@router.post("",
             summary="슬롯 추가",
             description="슬롯을 추가합니다. ISO8601 포맷 작성시 TIME ZONE에 유의하세요!! TIME ZONE이 없으면 UTC로 간주합니다.",
             status_code=status.HTTP_201_CREATED,
             response_model=MessageResponseModel
             )
async def add_new_slot(
        slot: SlotForm,
        user: User = Depends(verify_admin),
        service=InjectAdminService
):
    start_at = slot.start_at
    end_at = slot.end_at

    if slot.start_at.tzinfo is None:
        start_at = slot.start_at.replace(tzinfo=UTC)
    if slot.end_at.tzinfo is None:
        end_at = slot.end_at.replace(tzinfo=UTC)

    await service.add_exam_slot(
        Slot.create_with_time_range(start_time=start_at, end_time=end_at)
    )
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content=jsonable_encoder(
            MessageResponseModel(
                message="슬롯 추가에 성공했습니다.",
            )
        )
    )
