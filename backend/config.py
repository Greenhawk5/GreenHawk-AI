import os
from pathlib import Path
from dotenv import load_dotenv


load_dotenv()


BASE_DIR = Path(__file__).resolve().parent



APP_NAME = os.getenv(
    "APP_NAME",
    "AI Image Colorization API"
)


APP_VERSION = os.getenv(
    "APP_VERSION",
    "1.0"
)



HF_SPACE_FLUX = os.getenv(
    "HF_SPACE_FLUX"
)



_storage_dir = Path(os.getenv("STORAGE_DIR", "storage"))
STORAGE_DIR = (_storage_dir if _storage_dir.is_absolute() else BASE_DIR / _storage_dir).resolve()


CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        ",".join((
            "http://127.0.0.1:5500",
            "http://localhost:5500",
            "http://127.0.0.1:5173",
            "http://localhost:5173",
        ))
    ).split(",")
    if origin.strip()
]



FLUX_QUOTA_SECONDS = int(
    os.getenv(
        "FLUX_QUOTA_SECONDS",
        15
    )
)


FLUX_DAILY_LIMIT = int(
    os.getenv(
        "FLUX_DAILY_LIMIT",
        90
    )
)
