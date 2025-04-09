class NoSuchElementException(Exception):
    def __init__(self, elem_name: str, condition: str):
        self.elem_name = elem_name
        self.condition = condition
        self.message = f"{condition} 조건을 가진 {elem_name}이 존재하지 않습니다."
        super().__init__(self.message)

    def __str__(self):
        return self.message
