import bcrypt
from jose import jwt
from datetime import datetime, timedelta

SECRET_KEY = "tax-intel-secret-key"
ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8")
    )


def create_admin_token(username: str):
    payload = {
        "sub": username,
        "role": "admin",
        "exp": datetime.utcnow() + timedelta(hours=8)
    }

    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)