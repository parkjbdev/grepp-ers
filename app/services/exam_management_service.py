import logging
from abc import ABC, abstractmethod

from asyncpg import ExclusionViolationError

from app.models.reservation_model import Reservation
from app.models.slot_model import Slot
from app.repositories.reservation.dbimpl import ReservationRepository
from app.repositories.reservation.exceptions import SlotLimitExceededException
from app.repositories.slot.dbimpl import SlotRepository


class ExamManagementService(ABC):
    @abstractmethod
    def add_exam_slot(self, slot: Slot): pass

    @abstractmethod
    def add_reservation(self, reservation: Reservation): pass

    @abstractmethod
    def modify_reservation(self, reservation: Reservation): pass

    @abstractmethod
    def delete_reservation(self, reservation_id: int): pass

    @abstractmethod
    def confirm_reservation(self, reservation_id: int): pass


class ExamManagementServiceImpl(ExamManagementService):
    def __init__(self, slot_repo: SlotRepository, reservation_repo: ReservationRepository):
        self.slot_repo = slot_repo
        self.reservation_repo = reservation_repo
        self.__logger = logging.getLoggerClass()

    def get_exam_slots(self):
        return self.slot_repo.find()

    def add_exam_slot(self, slot: Slot):
        try:
            self.slot_repo.insert(slot)
        except ExclusionViolationError as e:
            self.__logger.exception(
                f"Time slot conflict: The time range {slot.time_range} overlaps with an existing slot")
            raise
        except Exception as e:
            self.__logger.exception(f"Unknown Exception: {e}")

    def add_reservation(self, reservation: Reservation):
        try:
            self.reservation_repo.insert(reservation)
        except SlotLimitExceededException as e:
            self.__logger.exception(
                f"Slot limit exceeded: The slot limit 50000 exceeded"
            )
            raise

    def modify_reservation(self, reservation: Reservation):
        # TODO: admin can modify both confirmed/unconfirmed reservation
        # TODO: user can modify only user's own unconfirmed reservation
        self.reservation_repo.modify(reservation)

    def delete_reservation(self, reservation_id: int):
        # TODO: admin can delete both confirmed/unconfirmed reservation
        # TODO: user can delete only user's own unconfirmed reservation
        self.reservation_repo.delete(reservation_id)

    # Admin
    def confirm_reservation(self, reservation_id: int):
        # TODO: only admin can confirm reservation
        self.reservation_repo.confirm_by_id(reservation_id)
