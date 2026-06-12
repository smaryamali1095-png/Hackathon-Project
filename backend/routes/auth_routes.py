from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from connection.database import db
from utils.auth_utils import hash_password, verify_password, create_admin_token

router = APIRouter()


class AdminRegister(BaseModel):
    username: str
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


@router.post("/register-admin")
async def register_admin(user: AdminRegister):
    existing = await db.users.find_one({"username": user.username})

    if existing:
        raise HTTPException(status_code=400, detail="Admin already exists")

    await db.users.insert_one({
        "username": user.username,
        "password": hash_password(user.password),
        "role": "admin"
    })

    return {
        "message": "Admin registered successfully",
        "username": user.username,
        "role": "admin"
    }


@router.post("/login")
async def login(user: UserLogin):
    found_user = await db.users.find_one({"username": user.username})

    if not found_user:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    if not verify_password(user.password, found_user["password"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = create_admin_token(found_user["username"])

    return {
        "status": "success",
        "username": found_user["username"],
        "role": "admin",
        "token": token
    }