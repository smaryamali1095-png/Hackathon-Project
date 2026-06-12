from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from connection.database import db
from utils.auth_utils import verify_password

router = APIRouter()


class UserLogin(BaseModel):
    username: str
    password: str


@router.post("/login")
async def login(user: UserLogin):
    found_user = await db.users.find_one({"username": user.username})

    if found_user and verify_password(user.password, found_user["password"]):
        return {"status": "success", "user": found_user["username"]}

    raise HTTPException(status_code=401, detail="Invalid username or password")