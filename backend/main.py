from fastapi import FastAPI
from routes.auth_routes import router as auth_router
from routes.data_routes import router as data_router
from ingestion.demo_loader import run_demo_loader

app = FastAPI(title="Tax Intel AI Backend")

# Include routers
app.include_router(auth_router, prefix="/auth", tags=["Auth"])
app.include_router(data_router, prefix="/data", tags=["Data"])

@app.get("/")
def home():
    return {"message": "Tax Intel AI Backend Online"}

# Startup event to initialize data
@app.on_event("startup")
async def startup_event():
    """
    Initializes the system by loading demo data if the system is fresh.
    """
    try:
        print("🚀 Initializing data pipeline...")
        await run_demo_loader()
        print("✅ Demo dataset loaded successfully.")
    except Exception as e:
        print(f"❌ Startup Error: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)