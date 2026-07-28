"""Serve user-uploaded media reliably under Daphne/ASGI (incl. non-ASCII paths)."""

from __future__ import annotations

from pathlib import Path

from django.conf import settings
from django.http import FileResponse, Http404, HttpRequest, HttpResponse


def serve_media(request: HttpRequest, path: str) -> HttpResponse:
    # Use the same storage backend ImageField writes to — avoids Windows path
    # encoding mismatches with django.views.static.serve + Cyrillic folders.
    from django.core.files.storage import default_storage

    normalized = path.replace("\\", "/").lstrip("/")
    if ".." in normalized.split("/"):
        raise Http404()
    if not default_storage.exists(normalized):
        raise Http404()

    # Prefer storage.open so FileSystemStorage resolves MEDIA_ROOT correctly.
    handle = default_storage.open(normalized, "rb")
    content_type = _guess_type(normalized)
    return FileResponse(handle, content_type=content_type)


def _guess_type(path: str) -> str:
    suffix = Path(path).suffix.lower()
    return {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".webp": "image/webp",
        ".svg": "image/svg+xml",
    }.get(suffix, "application/octet-stream")
