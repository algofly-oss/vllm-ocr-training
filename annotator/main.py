from fastapi import FastAPI, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from starlette.requests import Request as StarletteRequest
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import mimetypes

import os

app = FastAPI()


class CacheControlMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        if "static/images/" in request.url.path:
            mime_type, _ = mimetypes.guess_type(request.url.path)
            if mime_type and mime_type.startswith("image/"):
                response.headers["Cache-Control"] = "public, max-age=86400"
        return response


app.add_middleware(CacheControlMiddleware)

IMG_DIR = "static/images"
IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

os.makedirs(IMG_DIR, exist_ok=True)

image_list = sorted(
    [f for f in os.listdir(IMG_DIR) if os.path.splitext(f)[1].lower() in IMG_EXTS]
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/")
async def root():
    return RedirectResponse(url="/annotate/0")


@app.get("/annotate/{idx}")
async def get_annotate(request: Request, idx: int):
    if idx < 0 or idx >= len(image_list):
        return RedirectResponse(url="/annotate/0")

    img_file = image_list[idx]
    txt_file = os.path.splitext(img_file)[0] + ".txt"
    txt_path = os.path.join(IMG_DIR, txt_file)

    ocr_value = ""
    if os.path.exists(txt_path):
        with open(txt_path, "r") as f:
            ocr_value = f.read().strip()

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "image_file": f"/static/images/{img_file}",
            "ocr_text": ocr_value,
            "idx": idx,
            "total": len(image_list),
        },
    )


@app.post("/annotate/{idx}")
async def post_annotate(
    request: Request, idx: int, ocr_text: str = Form(...), direction: str = Form(...)
):
    img_file = image_list[idx]
    txt_file = os.path.splitext(img_file)[0] + ".txt"
    txt_path = os.path.join(IMG_DIR, txt_file)

    with open(txt_path, "w") as f:
        f.write(ocr_text.strip())

    if direction == "next" and idx < len(image_list) - 1:
        return RedirectResponse(url=f"/annotate/{idx+1}", status_code=303)
    elif direction == "prev" and idx > 0:
        return RedirectResponse(url=f"/annotate/{idx-1}", status_code=303)
    return RedirectResponse(url=f"/annotate/{idx}", status_code=303)


@app.get("/validate/{idx}", response_class=HTMLResponse)
async def validate_label(request: Request, idx: int):
    # Refresh file list every time to reflect deletions
    validated_list = sorted(
        [
            f
            for f in os.listdir(IMG_DIR)
            if os.path.splitext(f)[1].lower() in IMG_EXTS
            and os.path.exists(os.path.join(IMG_DIR, os.path.splitext(f)[0] + ".txt"))
        ]
    )

    if not validated_list:
        return HTMLResponse("<h2>No labeled images available for validation.</h2>")

    if idx < 0 or idx >= len(validated_list):
        return RedirectResponse(url="/validate/0", status_code=303)

    img_file = validated_list[idx]
    txt_file = os.path.splitext(img_file)[0] + ".txt"
    txt_path = os.path.join(IMG_DIR, txt_file)

    with open(txt_path, "r") as f:
        ocr_value = f.read().strip()

    return templates.TemplateResponse(
        "validate.html",
        {
            "request": request,
            "image_file": f"/static/images/{img_file}",
            "ocr_text": ocr_value,
            "idx": idx,
            "total": len(validated_list),
        },
    )


@app.get("/validate")
async def validate_page_redirect():
    return RedirectResponse(url="/validate/0")


@app.post("/validate/{idx}")
async def post_validate(request: Request, idx: int, action: str = Form(...)):
    validated_list = sorted(
        [
            f
            for f in os.listdir(IMG_DIR)
            if os.path.splitext(f)[1].lower() in IMG_EXTS
            and os.path.exists(os.path.join(IMG_DIR, os.path.splitext(f)[0] + ".txt"))
        ]
    )

    if idx < 0 or idx >= len(validated_list):
        return RedirectResponse(url="/validate/0", status_code=303)

    img_file = validated_list[idx]
    txt_file = os.path.splitext(img_file)[0] + ".txt"
    img_path = os.path.join(IMG_DIR, img_file)
    txt_path = os.path.join(IMG_DIR, txt_file)

    if action == "no":
        if os.path.exists(txt_path):
            os.remove(txt_path)
        if os.path.exists(img_path):
            os.remove(img_path)

    # Refresh the list after possible deletion
    updated_list = sorted(
        [
            f
            for f in os.listdir(IMG_DIR)
            if os.path.splitext(f)[1].lower() in IMG_EXTS
            and os.path.exists(os.path.join(IMG_DIR, os.path.splitext(f)[0] + ".txt"))
        ]
    )

    if action == "prev":
        new_idx = max(0, idx - 1)
    else:
        new_idx = idx + 1

    if new_idx >= len(updated_list):
        new_idx = 0

    return RedirectResponse(url=f"/validate/{new_idx}", status_code=303)


if __name__ == "__main__":
    os.system("uvicorn main:app --workers 4 --http h11 --host 0.0.0.0 --port 8000")
