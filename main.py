import logging

from fastapi import FastAPI, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.templating import Jinja2Templates

from flow import create_lookup_flow, create_image_delivery_flow

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(name)s  %(levelname)s  %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Inline CSAM Image Lookup",
    description="Look up CSAM images by Visual ID (VID).",
    version="1.0.0",
)

templates = Jinja2Templates(directory="templates")


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.get("/lookup")
async def lookup(vid: str = Query(..., description="Visual ID to look up")):
    shared = {
        "request": {"vid": vid.strip(), "image_id": None},
        "validation": {"input_present": False, "errors": []},
        "manufacturing": {"aries_results": [], "image_path_results": []},
        "filesystem": {
            "matched_images": [],
        },
        "response": {"lookup_result": None, "error": None},
    }

    try:
        lookup_flow = create_lookup_flow()
        lookup_flow.run(shared)
    except Exception:
        logger.exception("Lookup flow failed for VID=%s", vid)
        return JSONResponse(
            status_code=503,
            content={
                "vid": vid,
                "status": "error",
                "message": "An infrastructure error occurred. Please try again later.",
                "manufacturing": {},
                "directories": [],
                "images": [],
            },
        )

    result = shared["response"].get("lookup_result", {})
    if result.get("status") == "error":
        msg = result.get("message", "")
        if "not found" in msg.lower():
            status_code = 404
        elif "required" in msg.lower():
            status_code = 400
        else:
            status_code = 404
        return JSONResponse(status_code=status_code, content=result)

    return JSONResponse(status_code=200, content=result)


@app.get("/image/{image_id}")
async def get_image(image_id: str):
    shared = {
        "request": {"image_id": image_id},
        "filesystem": {"resolved_image": None},
        "image": {"binary_content": None, "mime_type": None},
        "response": {"error": None, "image_result": None},
    }

    try:
        image_flow = create_image_delivery_flow()
        image_flow.run(shared)
    except Exception:
        logger.exception("Image delivery failed for image_id=%s", image_id)
        return JSONResponse(
            status_code=503,
            content={"status": "error", "message": "Failed to load image."},
        )

    img_result = shared["response"].get("image_result", {})
    if img_result.get("error"):
        return JSONResponse(
            status_code=404,
            content={"status": "error", "message": img_result["error"]},
        )

    return Response(
        content=img_result["binary_content"],
        media_type=img_result.get("mime_type", "image/png"),
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
