from datetime import datetime, timedelta

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from config import JWT_ALGORITHM, JWT_EXPIRE_MINUTES, JWT_PREVIOUS_SECRETS, JWT_SECRET
from database import get_db
from models import User

security = HTTPBearer(auto_error=False)


def create_access_token(user_id: str, is_admin: bool = False) -> str:
    expire = datetime.utcnow() + timedelta(minutes=JWT_EXPIRE_MINUTES)
    return jwt.encode({"sub": user_id, "admin": is_admin, "exp": expire, "type": "access"}, JWT_SECRET, algorithm=JWT_ALGORITHM)


def create_refresh_token(user_id: str, family: str, expire_days: int = 7) -> str:
    expire = datetime.utcnow() + timedelta(days=expire_days)
    return jwt.encode({"sub": user_id, "family": family, "exp": expire, "type": "refresh"}, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_token(token: str) -> dict:
    for secret in [JWT_SECRET, *JWT_PREVIOUS_SECRETS]:
        try:
            return jwt.decode(token, secret, algorithms=[JWT_ALGORITHM])
        except JWTError:
            continue
    raise HTTPException(status_code=401, detail="token 无效或已过期")


def _resolve_access_payload(request: Request, credentials: HTTPAuthorizationCredentials | None) -> dict:
    from utils.file_access import collect_request_tokens

    for token in collect_request_tokens(request, credentials, request.query_params.get("token", "")):
        try:
            payload = verify_token(token)
        except HTTPException:
            continue
        if payload.get("type") == "access":
            return payload
    raise HTTPException(status_code=401, detail="缺少有效的访问凭证")


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db),
):
    payload = _resolve_access_payload(request, credentials)
    user = db.query(User).filter(User.id == payload["sub"]).first()
    if not user or user.status in ("banned", "deleted"):
        raise HTTPException(status_code=403, detail="账号已封禁或删除")
    return user


def get_admin_user(current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return current_user


def get_vip_user(current_user: User = Depends(get_current_user)):
    if current_user.is_admin:
        return current_user
    if not current_user.vip_expires_at or current_user.vip_expires_at < datetime.utcnow():
        raise HTTPException(status_code=403, detail="需要VIP会员")
    return current_user
