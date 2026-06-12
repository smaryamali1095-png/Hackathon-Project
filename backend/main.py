from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.auth_routes import router as auth_router
from routes.data_routes import router as data_router
from ingestion.demo_loader import run_demo_loader
from connection.database import check_mongo_connection

app = FastAPI(title="Tax Intel AI Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/auth", tags=["Auth"])
app.include_router(data_router, prefix="/data", tags=["Data"])


@app.get("/")
def home():
    return {"message": "Tax Intel AI Backend Online"}


@app.on_event("startup")
async def startup_event():
    print("🚀 Checking database connection...")

    mongo_ok = await check_mongo_connection()

    if not mongo_ok:
        print("⚠️ MongoDB not connected. Skipping demo loader.")
        return

    try:
        print("🚀 Initializing data pipeline...")
        await run_demo_loader()
        print("✅ Demo dataset loaded successfully.")
    except Exception as e:
        print(f"❌ Startup Error: {e}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )