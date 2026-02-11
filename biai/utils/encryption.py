"""Fernet encryption for sensitive data like passwords."""

from cryptography.fernet import Fernet


def generate_key() -> str:
    """Generate a new Fernet encryption key."""
    return Fernet.generate_key().decode()


def encrypt_value(value: str, key: str) -> str:
    """Encrypt a string value."""
    if not key:
        return value
    f = Fernet(key.encode() if isinstance(key, str) else key)
    return f.encrypt(value.encode()).decode()


def decrypt_value(encrypted: str, key: str) -> str:
    """Decrypt an encrypted string value."""
    if not key:
        return encrypted
    f = Fernet(key.encode() if isinstance(key, str) else key)
    return f.decrypt(encrypted.encode()).decode()
