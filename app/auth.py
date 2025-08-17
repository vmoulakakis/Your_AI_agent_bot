import os
import hashlib
from typing import Optional

from . import repositories as repo


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    salt_hex = salt.hex()
    h = hashlib.sha256(salt + password.encode("utf-8")).hexdigest()
    return f"sha256${salt_hex}${h}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algo, salt_hex, hash_hex = stored.split("$")
        if algo != "sha256":
            return False
        salt = bytes.fromhex(salt_hex)
        computed = hashlib.sha256(salt + password.encode("utf-8")).hexdigest()
        return computed == hash_hex
    except Exception:
        return False


def ensure_default_admin() -> None:
    if repo.count_users() == 0:
        # Default credentials for first run (please change in Settings later)
        default_username = "admin"
        default_password_hash = hash_password("admin")
        repo.create_user(default_username, default_password_hash, is_admin=True)


def authenticate(username: str, password: str) -> bool:
    user = repo.get_user_by_username(username)
    if not user:
        return False
    return verify_password(password, user["password_hash"])