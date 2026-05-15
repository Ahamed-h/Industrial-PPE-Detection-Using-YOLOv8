from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import Response, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app.config import MAX_FILE_SIZE
from app.detector import PPEDetector
from app.alert import alert_system
from app.logging_config import logger

app = FastAPI(
    title="SafeGuard PPE Detection API",
    description="Real-time PPE compliance detection for construction sites",
    version="1.0.0"
)

# CORS — allows Streamlit to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load detector once at startup
detector = PPEDetector(model_path="model/best.pt")


@app.get("/")
def root():
    return {
        "status": "running",
        "service": "SafeGuard PPE Detection API",
        "version": "1.0.0",
        "endpoints": [
            "POST /detect/image",
            "GET /violations/log",
            "GET /violations/stats",
            "GET /health"
        ]
    }


@app.get("/health")
def health():
    return {"status": "healthy", "model_loaded": True}


@app.post("/detect/image")
async def detect_image(file: UploadFile = File(...)):
    """
    Upload an image. Returns annotated image with bounding boxes.
    Also logs violations if detected.
    """
    # Validate file type
    if not file.content_type.startswith("image/"):
        logger.warning("Invalid content type: %s", file.content_type)
        raise HTTPException(
            status_code=400,
            detail="File must be an image (jpg, jpeg, png)"
        )

    # Read file bytes
    image_bytes = await file.read()

    if len(image_bytes) == 0:
        logger.warning("Empty file upload")
        raise HTTPException(status_code=400, detail="Empty file")

    if len(image_bytes) > MAX_FILE_SIZE:
        logger.warning("File too large: %d bytes", len(image_bytes))
        raise HTTPException(
            status_code=400,
            detail="File too large. Max 10MB."
        )

    try:
        # Run detection
        annotated_bytes, summary = detector.detect_image(image_bytes)

        # Check and log violations
        alert = alert_system.check_and_log(summary, source="image_upload")

        # Return annotated image
        # Summary is in response headers so frontend can read it
        return Response(
            content=annotated_bytes,
            media_type="image/jpeg",
            headers={
                "X-Safety-Status": summary["safety_status"],
                "X-Total-Violations": str(summary["total_violations"]),
                "X-Total-Detections": str(summary["total_detections"]),
            }
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Detection failed: {str(e)}")


@app.post("/detect/image/json")
async def detect_image_json(file: UploadFile = File(...)):
    """
    Same as /detect/image but returns JSON summary instead of image.
    Use this when you need the detection data not the annotated image.
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    image_bytes = await file.read()

    try:
        _, summary = detector.detect_image(image_bytes)
        alert = alert_system.check_and_log(summary, source="image_upload")
        return JSONResponse(content={
            "summary": summary,
            "alert": alert
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/violations/log")
def get_violation_log(limit: int = 50):
    """Get recent violation log."""
    return {
        "violations": alert_system.get_violation_log(limit=limit),
        "total": len(alert_system.get_violation_log(limit=10000))
    }


@app.get("/violations/stats")
def get_stats():
    """Get overall violation statistics."""
    return alert_system.get_statistics()


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)