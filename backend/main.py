from datetime import datetime
from pathlib import Path
import shutil
import uuid

from fastapi import BackgroundTasks, File, FastAPI, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from PIL import Image

from config import APP_NAME, APP_VERSION, CORS_ORIGINS, STORAGE_DIR
from jobs.job_manager import create_job, get_job, update_job
from schemas.job import JobStatusResponse
from schemas.response import ColorizationStartResponse
from services.colorization_service import run_all_models
from services.storage_manager import UPLOAD_DIR, initialize_storage
from services.url_service import convert_path_to_url


MAX_UPLOAD_BYTES = 20 * 1024 * 1024
MODEL_PROGRESS = {"zhang": 40, "deoldify": 70, "flux": 95}
CONTENT_TYPE_EXTENSIONS = {
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


app = FastAPI(title=APP_NAME,
              version=APP_VERSION,
              docs_url=None,
              redoc_url=None,
              openapi_url=None
              )
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "YOUR DOMAIN HERE",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

initialize_storage()
app.mount("/files", StaticFiles(directory=str(STORAGE_DIR), html=False), name="files")


def log(message):
    print(f"[GreenHawk] {message}", flush=True)


def now_iso():
    return datetime.now().astimezone().isoformat()


def public_results(results):
    response = {}
    for model_name, result in results.items():
        if result["status"] == "completed":
            response[model_name] = {
                "status": "completed",
                "url": convert_path_to_url(result["path"]),
            }
        else:
            response[model_name] = {
                "status": "failed",
                "error": result.get("error", "Model processing failed"),
            }
    return response


def process_colorization(job_id, image_path):
    log(f"Job {job_id}: background processing started for {image_path}")
    try:
        update_job(job_id, status="processing", progress=10, started_at=now_iso())

        def on_model_complete(model_name, _model_result, current_results):
            model_status = _model_result["status"]
            log(
                f"Job {job_id}: {model_name} {model_status}; "
                f"updating progress to {MODEL_PROGRESS[model_name]}%"
            )
            update_job(
                job_id,
                status="processing",
                progress=MODEL_PROGRESS[model_name],
                results=public_results(current_results),
            )

        results = run_all_models(image_path, on_model_complete=on_model_complete)
        serialized_results = public_results(results)
        completed_at = now_iso()

        if any(result["status"] == "completed" for result in results.values()):
            update_job(
                job_id,
                status="completed",
                progress=100,
                results=serialized_results,
                completed_at=completed_at,
            )
            log(f"Job {job_id}: completed with available model results")
        else:
            update_job(
                job_id,
                status="failed",
                progress=95,
                results=serialized_results,
                error="All colorization models failed.",
                completed_at=completed_at,
            )
            log(f"Job {job_id}: failed because all model calls failed")
    except Exception as error:
        log(f"Job {job_id}: unexpected processing error: {error}")
        update_job(
            job_id,
            status="failed",
            error=str(error),
            completed_at=now_iso(),
        )


@app.get("/")
def home():
    return {"status": "running", "message": "AI Colorization API"}


@app.post("/colorize", response_model=ColorizationStartResponse)
async def colorize_image(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(
        ...,
        description="Supported formats: JPG, JPEG, PNG, WEBP",
    ),
):
    log(
        f"Upload received: filename={file.filename}, "
        f"content_type={file.content_type}, size={file.size}"
    )
    extension = CONTENT_TYPE_EXTENSIONS.get(file.content_type)
    if not extension:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Unsupported file format",
                "allowed_formats": ["jpg", "jpeg", "png", "webp"],
            },
        )

    if file.size is not None and file.size > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=400, detail="File is larger than 20 MB.")

    try:
        image = Image.open(file.file)
        image.verify()
    except Exception as error:
        raise HTTPException(
            status_code=400,
            detail={"error": "Invalid image file", "message": "Uploaded image is corrupted"},
        ) from error
    finally:
        file.file.seek(0)

    job_id = str(uuid.uuid4())
    input_path = Path(UPLOAD_DIR) / f"{job_id}{extension}"
    with input_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    input_url = convert_path_to_url(input_path)
    log(f"Upload stored at {input_path}")
    log(f"Input image URL: {input_url}")
    create_job(input_image_url=input_url, job_id=job_id)
    background_tasks.add_task(process_colorization, job_id, str(input_path))
    log(f"Job {job_id}: queued background processing")

    return {
        "success": True,
        "message": "Colorization started",
        "job_id": job_id,
        "status": "queued",
        "input_image": input_url,
    }


@app.get("/jobs/{job_id}", response_model=JobStatusResponse)
def job_status(job_id: str):
    job = get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    return {"success": True, **job}
