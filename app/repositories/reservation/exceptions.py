from app.repositories.exception import NoSuchElementException


class SlotLimitExceededException(Exception):
    def __init__(self):
        self.message = "The maximum number of slots for this time period has been exceeded"
        super().__init__(self.message)


class NoSuchReservationException(NoSuchElementException):
    def __init__(self, reservation_id: int):
        super().__init__(elem_name="Reservation", condition=f"id = {reservation_id}")


class ReservationAlreadyConfirmedException(Exception):
    def __init__(self, reservation_id: int):
        self.message = f"Reservation {reservation_id} is already confirmed. Only unconfirmed reservations can be modified by user. Ask admin to modify."
        super().__init__(self.message)


class UserMismatchException(Exception):
    def __init__(self, user_id: int):
        self.message = f"User ID {user_id} does not match the reservation. Only unconfirmed reservations can be deleted by user. Ask admin to delete."
        super().__init__(self.message)
