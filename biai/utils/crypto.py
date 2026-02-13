"""Encryption utilities for connection passwords."""

from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken

_BIAI_DIR = Path.home() / ".biai"
_KEY_FILE = _BIAI_DIR / ".key"


def _get_or_create_key() -> bytes:
    """Load or generate a Fernet key at ~/.biai/.key."""
    _BIAI_DIR.mkdir(parents=True, exist_ok=True)
    if _KEY_FILE.exists():
        return _KEY_FILE.read_bytes()
    key = Fernet.generate_key()
    _KEY_FILE.write_bytes(key)
    return key


def encrypt_password(password: str) -> str:
    """Encrypt a password. Returns empty string for empty input."""
    if not password:
        return ""
    f = Fernet(_get_or_create_key())
    return f.encrypt(password.encode()).decode()


def decrypt_password(token: str) -> str:
    """Decrypt a password token. Returns empty string on failure."""
    if not token:
        return ""
    try:
        f = Fernet(_get_or_create_key())
        return f.decrypt(token.encode()).decode()
    except (InvalidToken, Exception):
        return ""
