from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.auth.auth_user import verify_admin
from app.dependencies.config import admin_exam_management_service, exam_management_service
from app.models.slot_model import Slot, SlotForResponse
from app.models.user_model import User
from app.repositories.slot.exceptions import SlotTimeRangeOverlapped
from app.services.admin.admin_service_impl import AdminExamManagementService
from app.services.user.user_service_impl import ExamManagementService

router = APIRouter(prefix="/slots", tags=["Slots"])

InjectService: ExamManagementService = Depends(exam_management_service)
InjectAdminService: AdminExamManagementService = Depends(admin_exam_management_service)


@router.get("", status_code=status.HTTP_200_OK, response_model=List[SlotForResponse])
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
        return list(map(lambda x: SlotForResponse.from_slot_with_amount(x), rows))
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date format",
        )


class SlotForm(BaseModel):
    start_at: datetime
    end_at: datetime


@router.post("", status_code=status.HTTP_201_CREATED)
async def add_new_slot(
        slot: SlotForm,
        user: User = Depends(verify_admin),
        service=InjectAdminService
):
    try:
        await service.add_exam_slot(
            Slot.create_with_time_range(start_time=slot.start_at, end_time=slot.end_at)
        )
    except SlotTimeRangeOverlapped as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Slot already exists",
        )
    return
