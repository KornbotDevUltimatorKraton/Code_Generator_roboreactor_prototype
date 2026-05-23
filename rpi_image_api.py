from fastapi import FastAPI, BackgroundTasks, Request
from pydantic import BaseModel, EmailStr

import subprocess
import uuid
import os
from typing import Dict


app = FastAPI()

# In-memory status store: {(email, project): {status, image_name}}
status_store: Dict[str, Dict] = {}

# Directory where the script and images are stored
WORK_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPT_PATH = os.path.join(WORK_DIR, "create_rpi_image.sh")

class ProjectRequest(BaseModel):
    email: EmailStr
    project: str


def run_script_and_update_status(email: str, project: str, image_name: str):
    key = f"{email}:{project}"
    script_cmd = ["sudo", "bash", SCRIPT_PATH]
    env = os.environ.copy()
    env["IMAGE_NAME"] = image_name
    try:
        status_store[key]["status"] = "in-progress"
        result = subprocess.run(script_cmd, env=env, cwd=WORK_DIR, capture_output=True, text=True)
        if result.returncode == 0:
            status_store[key]["status"] = "completed"
        else:
            status_store[key]["status"] = f"failed: {result.stderr.strip()}"
    except Exception as e:
        status_store[key]["status"] = f"error: {str(e)}"

@app.post("/generate-image/")
def generate_image(req: ProjectRequest, background_tasks: BackgroundTasks):
    key = f"{req.email}:{req.project}"
    image_name = f"rpi_clone_{uuid.uuid4().hex}.img"
    status_store[key] = {"status": "queued", "image_name": image_name}
    background_tasks.add_task(run_script_and_update_status, req.email, req.project, image_name)
    return {"status": "queued", "image_name": image_name}


@app.get("/status/")
def get_status(email: str, project: str):
    key = f"{email}:{project}"
    if key in status_store:
        return status_store[key]
    return {"status": "not-found"}

@app.get("/")
def root():
    return {"message": "Raspberry Pi Image Generator API"}
