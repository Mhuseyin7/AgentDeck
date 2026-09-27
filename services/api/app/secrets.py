"""Authenticated secret encryption. Key material must come from a KMS-managed environment variable."""

from cryptography.fernet import Fernet, InvalidToken


class SecretCipher:
    def __init__(self, master_key: str) -> None:
        if master_key.startswith("replace-with-"):
            raise RuntimeError("FERNET_MASTER_KEY must be configured before secrets can be stored")
        self._fernet = Fernet(master_key.encode("utf-8"))

    def encrypt(self, value: str) -> bytes:
        return self._fernet.encrypt(value.encode("utf-8"))

    def decrypt(self, ciphertext: bytes) -> str:
        try:
            return self._fernet.decrypt(ciphertext).decode("utf-8")
        except InvalidToken as exc:
            raise ValueError("secret ciphertext could not be authenticated") from exc
