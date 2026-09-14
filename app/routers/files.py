"""
Роуты для списка, загрузки и скачивания файлов.
"""
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse

from config import MAX_UPLOAD_SIZE, UPLOAD_DIR
from app.services.storage import (
    FileTooLargeError,
    delete_files,
    get_file_path,
    list_files,
    save_upload,
)

router = APIRouter(prefix="", tags=["files"])


@router.get("/files")
def get_files(
    limit: int | None = Query(None, ge=1),
    ext: str | None = Query(None, description="Фильтр по расширению файла, например 'jpeg'"),
    exclude_empty: bool = Query(False, description="Исключить битые файлы весом 0 байт"),
):
    """Список файлов в хранилище."""
    return list_files(UPLOAD_DIR, limit=limit, ext=ext, exclude_empty=exclude_empty)


def _media_type_for_preview(filename: str) -> str:
    ext = Path(filename).suffix.lower()
    if ext == ".pdf":
        return "application/pdf"
    if ext in (".jpg", ".jpeg"):
        return "image/jpeg"
    if ext == ".png":
        return "image/png"
    if ext == ".gif":
        return "image/gif"
    if ext == ".webp":
        return "image/webp"
    if ext == ".svg":
        return "image/svg+xml"
    if ext == ".bmp":
        return "image/bmp"
    return "application/octet-stream"


@router.get("/download/{filename}")
def download_file(
    filename: str,
    preview: bool = Query(False, description="Отдать файл для отображения в браузере (inline)"),
):
    """Скачать файл по имени. ?preview=1 — отображение в iframe/img без скачивания."""
    file_path = get_file_path(UPLOAD_DIR, filename)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    if preview:
        return FileResponse(
            path=file_path,
            filename=file_path.name,
            media_type=_media_type_for_preview(filename),
            content_disposition_type="inline",
        )
    return FileResponse(
        path=file_path,
        filename=file_path.name,
        media_type="application/octet-stream",
    )


@router.post("/upload")
def upload_files(files: list[UploadFile] = File(..., description="Один или несколько файлов")):
    """Загрузить один или несколько файлов. Конфликты по имени возвращаются в errors."""
    uploaded = []
    errors = []
    for file in files:
        safe_name = Path(file.filename).name
        if not safe_name:
            errors.append({"filename": file.filename or "", "detail": "Filename required"})
            continue
        try:
            path = save_upload(UPLOAD_DIR, safe_name, file.file, max_size=MAX_UPLOAD_SIZE)
            uploaded.append({"filename": safe_name, "saved_to": str(path)})
        except FileExistsError:
            errors.append({"filename": safe_name, "detail": "File already exists"})
        except FileTooLargeError:
            errors.append({"filename": safe_name, "detail": "File too large"})
    return {"uploaded": uploaded, "errors": errors}


@router.delete("/files")
def delete_files_endpoint(names: str = Query(..., description="Имена файлов через запятую")):
    """Удалить файлы по именам (одно или несколько через запятую)."""
    name_list = [n.strip() for n in names.split(",") if n.strip()]
    if not name_list:
        raise HTTPException(status_code=400, detail="At least one filename required")
    deleted = delete_files(UPLOAD_DIR, name_list)
    return {"deleted": deleted}
