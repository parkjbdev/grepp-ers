class UserNameAlreadyExistsException(Exception):
    def __init__(self, username: str):
        self.username = username
        self.message = f"User with username {username} already exists"
        super().__init__(self.message)


class NoSuchUserException(Exception):
    def __init__(self, condition: str):
        self.condition = condition
        self.message = f"User with {condition} does not exist"
        super().__init__(self.message)


