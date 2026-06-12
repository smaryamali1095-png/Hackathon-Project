from fastapi import APIRouter, UploadFile, File, HTTPException
import shutil
from services.citizen_service import process_csv_file
from connection.database import db # Assuming your MongoDB connection is here

router = APIRouter()

@router.post("/upload/{dataset_type}")
async def upload_dataset(dataset_type: str, file: UploadFile = File(...)):
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed.")
    
    # Save temporarily
    temp_path = f"temp_{file.filename}"
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    try:
        # Process and Clean
        cleaned_data = process_csv_file(temp_path)
        
        # Upsert into MongoDB
        collection = db[dataset_type]
        for record in cleaned_data:
            # Upsert using CNIC as the unique identifier
            collection.update_one(
                {"cnic": record["cnic"]},
                {"$set": record},
                upsert=True
            )
            
        return {"message": f"Successfully processed {len(cleaned_data)} records into {dataset_type}"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))