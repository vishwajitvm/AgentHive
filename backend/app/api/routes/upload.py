from fastapi import APIRouter, UploadFile, File, HTTPException
import httpx
from app.core.config import settings

router = APIRouter()

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    # Sanitize filename against path traversal (Advanced Security)
    import os
    safe_filename = os.path.basename(file.filename)
    safe_filename = "".join(c for c in safe_filename if c.isalnum() or c in " ._-")
    if not safe_filename:
        raise HTTPException(status_code=400, detail="Invalid filename")

    minio_url = f"http://{settings.minio_endpoint}/{settings.minio_bucket}/{safe_filename}"
    auth = httpx.BasicAuth(settings.minio_access_key, settings.minio_secret_key)
    
    try:
        content = await file.read()
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.put(minio_url, content=content, auth=auth)
            if resp.status_code in [200, 201]:
                return {"message": "File uploaded successfully", "filename": file.filename, "url": minio_url}
            else:
                raise HTTPException(status_code=500, detail=f"Failed to upload to MinIO: {resp.text}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
