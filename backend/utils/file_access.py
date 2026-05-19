from pathlib import Path, PurePosixPath

from fastapi import HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from auth import verify_token
from config import ACCESS_TOKEN_COOKIE_NAMES, UPLOAD_DIR
from models import User

UPLOAD_ROOT = Path(UPLOAD_DIR).resolve()


def normalize_upload_relative_path(raw_path: str) -> str:
    text = str(raw_path or "").strip().replace("\\", "/")
    if not text:
        raise HTTPException(400, "文件路径不能为空")
    if text.startswith(("http://", "https://", "file://")):
        raise HTTPException(400, "不支持外部文件路径")

    pure_path = PurePosixPath("/" + text.lstrip("/"))
    parts = [part for part in pure_path.parts if part not in ("", "/")]
    if not parts or any(part in (".", "..") for part in parts):
        raise HTTPException(400, "非法文件路径")
    if ":" in parts[0]:
        raise HTTPException(400, "非法文件路径")
    return "/" + "/".join(parts)


def resolve_upload_path(raw_path: str, *, allowed_prefixes: tuple[str, ...] | None = None) -> Path:
    relative_path = normalize_upload_relative_path(raw_path)
    parts = [part for part in relative_path.strip("/").split("/") if part]
    if allowed_prefixes and (not parts or parts[0] not in allowed_prefixes):
        raise HTTPException(403, "无权访问该文件")

    full_path = (UPLOAD_ROOT.joinpath(*parts)).resolve()
    try:
        full_path.relative_to(UPLOAD_ROOT)
    except ValueError as exc:
        raise HTTPException(400, "非法文件路径") from exc
    return full_path


def collect_request_tokens(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = None,
    query_token: str = "",
    preferred_cookie_names: tuple[str, ...] = ACCESS_TOKEN_COOKIE_NAMES,
) -> list[str]:
    tokens: list[str] = []
    if credentials and credentials.credentials:
        tokens.append(credentials.credentials.strip())
    if query_token:
        tokens.append(str(query_token).strip())
    for cookie_name in preferred_cookie_names:
        cookie_token = (request.cookies.get(cookie_name) or "").strip()
        if cookie_token:
            tokens.append(cookie_token)
    for cookie_name in ("access_token",):
        cookie_token = (request.cookies.get(cookie_name) or "").strip()
        if cookie_token:
            tokens.append(cookie_token)

    deduped: list[str] = []
    for token in tokens:
        if token and token not in deduped:
            deduped.append(token)
    return deduped


def get_request_user(
    request: Request,
    db: Session,
    credentials: HTTPAuthorizationCredentials | None = None,
    query_token: str = "",
) -> User:
    for token in collect_request_tokens(request, credentials, query_token):
        try:
            payload = verify_token(token)
        except HTTPException:
            continue
        if payload.get("type") != "access":
            continue
        user = db.query(User).filter(User.id == payload["sub"]).first()
        if not user or user.status in ("banned", "deleted"):
            continue
        return user
    raise HTTPException(401, "token 无效或已过期")
