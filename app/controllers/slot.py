from datetime import datetime, timezone
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

router = APIRouter(prefix="/slots", tags=["슬롯"])

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
            content=jsonable_encoder(MessageResponseWithResultModel[List[SlotForResponse]](
                message="슬롯 조회에 성공했습니다.",
                result=list(map(lambda x: SlotForResponse.from_slot_with_amount(x), rows))
            ))
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date format",
        )


class SlotForm(BaseModel):
    start_at: datetime
    end_at: datetime


@router.post("",
             summary="슬롯 추가",
             description="슬롯을 추가합니다.",
             status_code=status.HTTP_201_CREATED,
             response_model=MessageResponseModel
             )
async def add_new_slot(
        slot: SlotForm,
        user: User = Depends(verify_admin),
        service=InjectAdminService
):
    await service.add_exam_slot(
        Slot.create_with_time_range(start_time=slot.start_at, end_time=slot.end_at)
    )
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content=MessageResponseModel(
            message="슬롯 추가에 성공했습니다.",
        )
    )
