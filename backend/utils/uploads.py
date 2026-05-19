import os
from typing import Iterable

from fastapi import HTTPException, UploadFile


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".webm", ".mkv", ".m4v"}
AUDIO_EXTENSIONS = {".mp3", ".wav", ".ogg", ".webm", ".m4a", ".aac"}


def _detect_kind(content: bytes) -> str | None:
    header = content[:32]
    if header.startswith(b"\xff\xd8\xff"):
        return "image"
    if header.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image"
    if header.startswith((b"GIF87a", b"GIF89a")):
        return "image"
    if header.startswith(b"BM"):
        return "image"
    if header.startswith(b"RIFF") and content[8:12] == b"WEBP":
        return "image"
    if header.startswith(b"RIFF") and content[8:12] == b"WAVE":
        return "audio"
    if header.startswith(b"OggS"):
        return "audio"
    if header.startswith(b"ID3"):
        return "audio"
    if len(header) >= 2 and header[0] == 0xFF and header[1] in {0xF1, 0xF3, 0xF9, 0xFB}:
        return "audio"
    if header.startswith(b"\x1A\x45\xDF\xA3"):
        return "video"
    if len(content) >= 12 and content[4:8] == b"ftyp":
        brand = content[8:12]
        if brand in {b"isom", b"iso2", b"mp41", b"mp42", b"avc1", b"qt  ", b"M4V ", b"MSNV"}:
            return "video"
        if brand in {b"M4A ", b"mp4a"}:
            return "audio"
    return None


def _normalize_extension(filename: str, fallback: str) -> str:
    ext = os.path.splitext(filename or "")[1].lower()
    return ext or fallback


def _allowed_extension(ext: str, allowed_extensions: Iterable[str]) -> bool:
    return ext.lower() in {item.lower() for item in allowed_extensions}


async def read_validated_upload(
    file: UploadFile,
    *,
    max_bytes: int,
    allowed_kinds: set[str],
    allowed_extensions: set[str],
    fallback_extension: str,
    label: str,
) -> dict:
    if not file or not file.filename:
        raise HTTPException(400, f"请选择{label}")

    content = await file.read()
    if not content:
        raise HTTPException(400, f"{label}不能为空")
    if len(content) > max_bytes:
        raise HTTPException(400, f"{label}大小不能超过 {max_bytes // (1024 * 1024)}MB")

    ext = _normalize_extension(file.filename, fallback_extension)
    if not _allowed_extension(ext, allowed_extensions):
        raise HTTPException(400, f"{label}格式不支持")

    reported_kind = (file.content_type or "").split("/", 1)[0].strip().lower()
    detected_kind = _detect_kind(content)
    if detected_kind is None and reported_kind in {"audio", "video"}:
        detected_kind = reported_kind
    elif ext == ".webm" and reported_kind in {"audio", "video"}:
        detected_kind = reported_kind
    if detected_kind not in allowed_kinds:
        raise HTTPException(400, f"{label}内容校验失败")

    return {
        "content": content,
        "ext": ext,
        "kind": detected_kind,
        "content_type": file.content_type or "",
    }
