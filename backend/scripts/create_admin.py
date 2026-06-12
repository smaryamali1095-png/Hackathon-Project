import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from connection.database import db
from utils.auth_utils import hash_password 

async def add_admin():
    # Hash the password using our new utility
    admin_data = {
        "username": "admin",
        "password": hash_password("Qwert123."),
        "role": "admin"
    }
    
    await db.users.insert_one(admin_data)
    print("✅ Admin user created successfully!")

if __name__ == "__main__":
    asyncio.run(add_admin())