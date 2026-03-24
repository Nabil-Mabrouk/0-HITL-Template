import os
import uuid
import aiofiles
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
from app.auth.dependencies import require_admin
from app.models import User

router = APIRouter(prefix="/admin/media", tags=["media"])

UPLOAD_DIR = "uploads"
MAX_SIZE   = 100 * 1024 * 1024  # 100MB

ALLOWED_TYPES = {
    # Images
    "image/jpeg": ".jpg", "image/png": ".png",
    "image/gif": ".gif",  "image/webp": ".webp",
    # Vidéos
    "video/mp4": ".mp4",  "video/webm": ".webm",
    # Audio
    "audio/mpeg": ".mp3", "audio/mp3": ".mp3",
    # Documents
    "application/pdf": ".pdf",
}

def get_media_type(filename: str) -> str:
    ext = filename.rsplit(".", 1)[-1].lower()
    types = {
        "jpg": "image", "jpeg": "image", "png": "image",
        "gif": "image", "webp": "image",
        "mp4": "video",  "webm": "video",
        "mp3": "audio",
        "pdf": "document",
    }
    return types.get(ext, "other")


@router.post("/upload")
async def upload_file(
    file:  UploadFile = File(...),
    admin: User       = Depends(require_admin),
):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400,
                            detail=f"Type non supporté : {file.content_type}")

    # Lire et vérifier la taille
    content = await file.read()
    if len(content) > MAX_SIZE:
        raise HTTPException(status_code=400,
                            detail="Fichier trop volumineux (max 100MB)")

    # Générer un nom unique
    ext      = ALLOWED_TYPES[file.content_type]
    filename = f"{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)

    async with aiofiles.open(filepath, "wb") as f:
        await f.write(content)

    return {
        "filename":   filename,
        "url":        f"/uploads/{filename}",
        "type":       get_media_type(filename),
        "size":       len(content),
        "original":   file.filename,
    }


@router.get("/list")
async def list_files(admin: User = Depends(require_admin)):
    files = []
    for fname in os.listdir(UPLOAD_DIR):
        fpath = os.path.join(UPLOAD_DIR, fname)
        if os.path.isfile(fpath):
            files.append({
                "filename": fname,
                "url":      f"/uploads/{fname}",
                "type":     get_media_type(fname),
                "size":     os.path.getsize(fpath),
            })
    # Trier par date de modification (plus récent en premier)
    files.sort(key=lambda f: os.path.getmtime(
        os.path.join(UPLOAD_DIR, f["filename"])), reverse=True)
    return {"files": files}


@router.delete("/{filename}")
async def delete_file(
    filename: str,
    admin:    User = Depends(require_admin),
):
    # Sécurité — empêcher path traversal
    if "/" in filename or "\\" in filename or ".." in filename:
        raise HTTPException(status_code=400, detail="Nom invalide")

    filepath = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Fichier introuvable")

    os.remove(filepath)
    return {"message": "Fichier supprimé"}