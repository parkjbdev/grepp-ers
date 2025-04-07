from app.repositories.exception import NoSuchElementException


class SlotLimitExceededException(Exception):
    def __init__(self, message="The maximum number of slots for this time period has been exceeded"):
        self.message = message
        super().__init__(self.message)

class NoSuchReservationException(NoSuchElementException):
    def __init__(self, reservation_id: int):
        super().__init__(elem_name="Reservation", condition=f"id = {reservation_id}")