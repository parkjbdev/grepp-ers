from app.repositories.exception import NoSuchElementException


class UserNameAlreadyExistsException(Exception):
    def __init__(self, username: str):
        self.message = f"User with username {username} already exists"
        super().__init__(self.message)

    def __str__(self):
        return self.message


class NoSuchUserException(NoSuchElementException):
    def __init__(self, condition: str):
        super().__init__(elem_name="User", condition=condition)
