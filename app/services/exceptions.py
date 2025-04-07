class DBUnknownException(Exception):
    def __init__(self, message="Unknown database error occurred. Couldn't finish the transaction."):
        self.message = message
        super().__init__(self.message)


class DBConflictException(Exception):
    def __init__(self, message="Database conflict error occurred."):
        self.message = message
        super().__init__(self.message)


class NotFoundException(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class UserNotFoundException(Exception):
    def __init__(self, username: str):
        self.username = username
        self.message = f"사용자 ID {username}를 찾을 수 없습니다"
        super().__init__(self.message)
