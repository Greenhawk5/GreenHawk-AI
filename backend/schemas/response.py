from pydantic import BaseModel


class ColorizationStartResponse(BaseModel):
    success: bool
    message: str
    job_id: str
    status: str
    input_image: str
