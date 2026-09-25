from cryptography.fernet import Fernet

from app.secrets import SecretCipher


def test_ciphertext_is_authenticated_and_reversible() -> None:
    cipher = SecretCipher(Fernet.generate_key().decode("utf-8"))
    encrypted = cipher.encrypt("only-for-authorized-task")
    assert b"only-for-authorized-task" not in encrypted
    assert cipher.decrypt(encrypted) == "only-for-authorized-task"
