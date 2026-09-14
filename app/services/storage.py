"""
Сервис работы с файловым хранилищем. Вся логика путей и FS вынесена сюда.
"""
from datetime import datetime
from pathlib import Path

CHUNK_SIZE = 1024 * 1024


class FileTooLargeError(Exception):
    """Загружаемый файл превышает допустимый размер."""


def list_files(
    upload_dir: Path,
    limit: int | None = None,
    ext: str | None = None,
    exclude_empty: bool = False,
) -> list[dict]:
    """
    Список файлов в директории.
    limit — макс. количество записей.
    ext — фильтр по расширению файла (например "jpeg" или ".jpeg"); без учёта регистра.
    exclude_empty — исключить файлы весом 0 байт ("битые" файлы).
    """
    normalized_ext = None
    if ext:
        normalized_ext = ext.lower()
        if not normalized_ext.startswith("."):
            normalized_ext = "." + normalized_ext

    files_data = []
    for f in upload_dir.iterdir():
        if not f.is_file():
            continue
        if normalized_ext is not None and f.suffix.lower() != normalized_ext:
            continue
        try:
            stat = f.stat()
        except FileNotFoundError:
            # Файл мог быть удалён параллельным запросом между iterdir() и stat()
            continue
        if exclude_empty and stat.st_size == 0:
            continue
        files_data.append({
            "name": f.name,
            "size": stat.st_size,
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        })
    files_data.sort(key=lambda x: x["name"])
    if limit is not None:
        files_data = files_data[:limit]
    return files_data


def get_file_path(upload_dir: Path, filename: str) -> Path:
    """Безопасный путь к файлу (без path traversal)."""
    safe_name = Path(filename).name
    return upload_dir / safe_name


def save_upload(upload_dir: Path, filename: str, source, max_size: int | None = None) -> Path:
    """
    Сохраняет содержимое source в upload_dir/filename, читая и записывая по частям
    (не блокируя event loop надолго на одном большом файле).
    Создаёт только если файл не существует (xb).
    Raises FileExistsError если файл уже есть.
    Raises FileTooLargeError если max_size задан и превышен — частично записанный файл удаляется.
    """
    path = get_file_path(upload_dir, filename)
    written = 0
    with path.open("xb") as buffer:
        while True:
            chunk = source.read(CHUNK_SIZE)
            if not chunk:
                break
            written += len(chunk)
            if max_size is not None and written > max_size:
                buffer.close()
                path.unlink(missing_ok=True)
                raise FileTooLargeError(f"File exceeds {max_size} bytes limit")
            buffer.write(chunk)
    return path


def delete_files(upload_dir: Path, names: list[str]) -> list[str]:
    """
    Удаляет файлы по именам. Имена нормализуются (без path traversal).
    Возвращает список имён файлов, которые были удалены (существовали и удалены).
    Несуществующие имена пропускаются.
    """
    deleted = []
    for raw_name in names:
        path = get_file_path(upload_dir, raw_name)
        if path.is_file():
            path.unlink()
            deleted.append(path.name)
    return deleted
