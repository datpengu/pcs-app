from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Query
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from camera_service import CameraService


STATIC_DIR = Path(__file__).parent / "static"
camera_service = CameraService()


@asynccontextmanager
async def lifespan(app):
    camera_service.start()
    yield
    camera_service.stop()


app = FastAPI(title="PCS App", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
def dashboard():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/stats")
def get_stats():
    return camera_service.stats()


@app.get("/api/history")
def get_history(days: int = Query(default=14, ge=1, le=90)):
    return {"days": camera_service.history(days)}


@app.get("/health")
def health():
    return {"status": camera_service.stats()["status"]}


@app.get("/stream.mjpg", include_in_schema=False)
def stream():
    return StreamingResponse(camera_service.mjpeg_stream(), media_type="multipart/x-mixed-replace; boundary=frame")
