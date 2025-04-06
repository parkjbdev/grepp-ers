from datetime import UTC, datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.auth_user import verify_admin
from app.dependencies.config import admin_exam_management_service, exam_management_service
from app.models.slot_model import Slot
from app.models.user_model import User
from app.services.admin_exam_management_service import AdminExamManagementService
from app.services.exam_management_service import ExamManagementService

router = APIRouter(prefix="/slots", tags=["Slots"])

InjectService: ExamManagementService = Depends(exam_management_service)
InjectAdminService: AdminExamManagementService = Depends(admin_exam_management_service)


@router.get("", status_code=status.HTTP_200_OK)
async def get_available_slots(
        start_at: datetime = datetime.now(UTC),
        end_at: Optional[datetime] = datetime.now(UTC) + timedelta(days=30),
        service=InjectService
):
    try:
        if start_at.tzinfo is None:
            start_at = start_at.replace(tzinfo=timezone.utc)
        if end_at.tzinfo is None:
            end_at = end_at.replace(tzinfo=timezone.utc)

        if start_at > end_at:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="start_at must be before end_at",
            )

        return await service.find_slots(start_at, end_at)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date format",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.post("", status_code=status.HTTP_201_CREATED)
async def add_new_slot(
        slot: Slot,
        user: User = Depends(verify_admin),
        service=InjectAdminService
):
    try:
        await service.add_exam_slot(slot)
    except Exception as e:
        raise
    return
