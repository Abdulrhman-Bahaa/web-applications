import shutil

from fastapi import FastAPI, File, UploadFile, Depends, HTTPException
import uvicorn
import hashlib
import pyzipper
from sqlalchemy.orm import Session
from database import engine, Base, get_db
from models import Sample
import os
from fastapi.responses import FileResponse
from pydantic import BaseModel
import redis

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)  # Make folder if it doesn't exist

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI()
# Connect to Redis
r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)


# Pydantic model for analysis status update
class AnalysisStatusUpdate(BaseModel):
    static_analysis: bool = None
    dynamic_analysis: bool = None


@app.get("/")
def read_root():
    return {"hello": "world"}


@app.post("/samples/upload/")
async def create_sample(file: UploadFile = File(...), db: Session = Depends(get_db)):

    # Read file content
    contents = await file.read()

    # Get original filename
    file_name = file.filename

    # Get file size and type
    file_size = len(contents)

    # Simple file type extraction from filename
    file_extension = os.path.splitext(file_name)[1].lstrip('.').lower()

    # Calculate hashes
    def calc_hash(file_bytes, algo):
        hash_func = hashlib.new(algo)
        hash_func.update(file_bytes)
        return hash_func.hexdigest()

    hash_md5 = calc_hash(contents, 'md5')
    hash_sha1 = calc_hash(contents, 'sha1')
    hash_sha256 = calc_hash(contents, 'sha256')

    # Create zip file path
    zip_filename = os.path.join(UPLOAD_DIR, f"{hash_sha256}.zip")

    # Create password-protected zip
    with pyzipper.AESZipFile(zip_filename, 'w', compression=pyzipper.ZIP_DEFLATED,
                             encryption=pyzipper.WZ_AES) as zipf:
        zipf.setpassword("infected".encode())  # set password
        zipf.writestr("sample", contents)  # add file to zip

    # Create Sample instance
    sample = Sample(
        hash_md5=hash_md5,
        hash_sha1=hash_sha1,
        hash_sha256=hash_sha256,
        file_name=file_name,
        file_size=file_size,
        file_type=file_extension
    )

    db.add(sample)
    db.commit()
    db.refresh(sample)
    return sample

# Get sample metadata by ID or SHA256 hash, and return the file if &download=1 is specified


@app.get("/samples/{identifier}")
def read_sample(identifier: str, download: int = 0, db: Session = Depends(get_db)):
    sample = None
    if len(identifier) == 64:  # SHA256 hash length
        if download == 1:
            zip_filename = os.path.join(UPLOAD_DIR, f"{identifier}.zip")
            if not os.path.exists(zip_filename):
                return {"error": "File not found"}
            return FileResponse(zip_filename, media_type='application/zip', filename=f"{identifier}.zip")

        sample = db.query(Sample).filter(
            Sample.hash_sha256 == identifier).first()
    elif identifier.isdigit():  # ID
        sample = db.query(Sample).filter(Sample.id == int(identifier)).first()
    if sample is None:
        return {"error": "Sample not found"}
    return sample


@app.get("/samples")
def read_samples(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    samples = db.query(Sample).offset(skip).limit(limit).all()
    return samples


@app.get("/samples/unanalyzed/first")
def read_first_unanalyzed_sample(db: Session = Depends(get_db)):
    """
    Returns the metadata of the first sample where either static_analysis 
    or dynamic_analysis equals zero/False, ordered by lowest id.
    """
    sample = db.query(Sample).filter(
        (Sample.static_analysis == False) | (Sample.dynamic_analysis == False)
    ).order_by(Sample.id.asc()).first()

    if sample is None:
        raise HTTPException(
            status_code=404, detail="No unanalyzed samples found")
    return sample


@app.post("/samples/{sha256}/analysis")
def update_sample_analysis(sha256: str, analysis_status: AnalysisStatusUpdate, db: Session = Depends(get_db)):
    """
    Updates the static_analysis and/or dynamic_analysis status for a sample by SHA256 hash.
    """
    sample = db.query(Sample).filter(Sample.hash_sha256 == sha256).first()

    if sample is None:
        return {"error": "Sample not found"}

    if analysis_status.static_analysis is not None:
        sample.static_analysis = analysis_status.static_analysis
    if analysis_status.dynamic_analysis is not None:
        sample.dynamic_analysis = analysis_status.dynamic_analysis

    db.commit()
    db.refresh(sample)
    return sample


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    contents = await file.read()

    # save to disk in uploads folder
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as f:
        f.write(contents)


# @app.post("/upload")
# async def upload_file(file: UploadFile = File(...)):
#     filename = Path(file.filename).name
#     file_path = os.path.join(UPLOAD_DIR, filename)

#     with open(file_path, "wb") as f:
#         shutil.copyfileobj(file.file, f)

#     return {"status": "ok", "filename": filename}


@app.get("/download/{filename}")
def download_file(filename: str):
    file_path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(file_path):
        return {"error": "File not found"}
    return FileResponse(file_path, media_type='application/octet-stream', filename=filename)


@app.get("/json/{filename}")
def get_file_as_json(filename: str):
    file_path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(file_path):
        return {"error": "File not found"}
    with open(file_path, "r") as f:
        content = f.read()
    return {"filename": filename, "content": content}


@app.get("/text/{filename}")
def get_file_as_text(filename: str):
    file_path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(file_path):
        return {"error": "File not found"}
    with open(file_path, "r") as f:
        content = f.read()
    return {"filename": filename, "content": content}


class ClientsRequest(BaseModel):
    clients: list[str]  # List of client strings


@app.post("/update_core/")
async def update_core(request: ClientsRequest):
    """
    Delete 'core', add provided clients to the set, and set expiration to 10 seconds.
    """
    # if not request.clients:
    #     raise HTTPException(
    #         status_code=400, detail="Clients list cannot be empty")

    try:
        # Use pipeline for atomic execution
        pipe = r.pipeline()
        pipe.delete("core")

        if request.clients:
            pipe.sadd("core", *request.clients)
        else:
            pipe.sadd("core", "")  # Add empty string if no clients provided

        pipe.expire("core", 6)
        pipe.execute()

        return {
            "status": "success",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/core")
def get_core_clients():
    """
    Retrieve all clients in the 'core' set.
    """
    try:
        if not r.exists("core"):
            return {
                "status": "failed",
                "clients": []
            }
        clients = r.smembers("core")
        # If the core set doesn't exist, raise a 404 error
        return {
            "status": "success",
            "clients": list(clients)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=5001)
