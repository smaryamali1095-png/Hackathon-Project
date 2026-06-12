from fastapi import Header, HTTPException
from jose import jwt, JWTError

SECRET_KEY = "tax-intel-secret-key"
ALGORITHM = "HS256"


def require_admin(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization token")

    try:
        token = authorization.replace("Bearer ", "")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        if payload.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Admin access required")

        return payload

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")