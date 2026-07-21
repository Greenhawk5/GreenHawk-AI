import uuid
from copy import deepcopy
from datetime import datetime
from threading import Lock


jobs = {}
jobs_lock = Lock()


def log(message):
    print(f"[JobManager] {message}", flush=True)


def create_job(input_image_url=None, job_id=None):
    """Create a thread-safe in-memory job using the supplied upload/job ID."""
    job_id = job_id or str(uuid.uuid4())

    with jobs_lock:
        jobs[job_id] = {
            "job_id": job_id,
            "status": "queued",
            "progress": 0,
            "input_image": input_image_url,
            "created_at": datetime.now().astimezone().isoformat(),
            "started_at": None,
            "completed_at": None,
            "results": {},
            "error": None,
        }

    log(f"Created job {job_id} for {input_image_url}")

    return job_id


def update_job(
    job_id,
    status=None,
    progress=None,
    results=None,
    error=None,
    started_at=None,
    completed_at=None,
):
    update_summary = None
    with jobs_lock:
        if job_id not in jobs:
            log(f"Ignored update for unknown job {job_id}")
            return

        if status is not None:
            jobs[job_id]["status"] = status
        if progress is not None:
            jobs[job_id]["progress"] = progress
        if results is not None:
            jobs[job_id]["results"] = results
        if error is not None:
            jobs[job_id]["error"] = error
        if started_at is not None:
            jobs[job_id]["started_at"] = started_at
        if completed_at is not None:
            jobs[job_id]["completed_at"] = completed_at

        if status is not None or progress is not None or error is not None:
            update_summary = (
                f"Job {job_id}: status={jobs[job_id]['status']}, "
                f"progress={jobs[job_id]['progress']}"
            )
            if error is not None:
                update_summary += f", error={error}"

    if update_summary:
        log(update_summary)


def get_job(job_id):
    with jobs_lock:
        job = jobs.get(job_id)
        return deepcopy(job) if job else None
