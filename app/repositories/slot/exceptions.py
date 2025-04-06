class SlotTimeRangeOverlapped(Exception):
    def __init__(self, time_range):
        super().__init__(f"Time range conflict: {time_range}")
        self.time_range = time_range
