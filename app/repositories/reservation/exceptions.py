from app.repositories.exception import NoSuchElementException


class SlotLimitExceededException(Exception):
    def __init__(self):
        self.message = "본 시험의 예약 가능 인원이 초과되어 실패하였습니다."
        super().__init__(self.message)


class NoSuchReservationException(NoSuchElementException):
    def __init__(self, reservation_id: int):
        super().__init__(elem_name="Reservation", condition=f"id = {reservation_id}")


class ReservationAlreadyConfirmedException(Exception):
    def __init__(self, reservation_id: int):
        self.message = f"{reservation_id}번 예약은 이미 확정되었습니다. 사용자가 수정할 수 있는 예약은 미확정 예약만 가능합니다. 관리자에게 수정 요청하세요."
        super().__init__(self.message)


class UserMismatchException(Exception):
    def __init__(self, user_id: int):
        # TODO: Replace with NoSuchReservationException for security?
        self.message = f"{user_id}번 사용자는 요청한 예약을 변경할 권한이 없습니다. 본인의 예약만 삭제할 권한이 있습니다."
        super().__init__(self.message)


class DaysNotLeftEnoughException(Exception):
    def __init__(self, days: int):
        self.message = f"예약은 시험으로부터 {days}일 이전에만 가능합니다."
        super().__init__(self.message)
