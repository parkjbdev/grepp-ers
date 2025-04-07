class NoSuchElementException(Exception):
    def __init__(self, elem_name: str, condition: str):
        self.elem_name = elem_name
        self.condition = condition
        self.message = f"{elem_name} with {condition} does not exist"
        super().__init__(self.message)
