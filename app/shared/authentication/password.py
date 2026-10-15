import bcrypt


class BcryptPasswordHasher:
    """bcrypt implementation of IPasswordHasher."""

    def __init__(self, rounds: int = 10):
        self._rounds = rounds

    def hash(self, password: str) -> str:
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt(self._rounds)).decode()

    def verify(self, password: str, password_hash: str) -> bool:
        try:
            return bcrypt.checkpw(password.encode(), password_hash.encode())
        except ValueError:
            # Malformed hash or password longer than 72 bytes
            return False
