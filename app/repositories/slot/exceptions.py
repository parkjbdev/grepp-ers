from app.repositories.exception import NoSuchElementException


class SlotTimeRangeOverlapped(Exception):
    def __init__(self, time_range):
        super().__init__(f"Time range conflict: {time_range}")
        self.time_range = time_range


class NoSuchSlotException(NoSuchElementException):
    def __init__(self, slot_id: int):
        super().__init__(elem_name="Slot", condition=f"id = {slot_id}")
