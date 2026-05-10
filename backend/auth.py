from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from config import JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRE_MINUTES
from database import get_db
from models import User

security = HTTPBearer()

def create_access_token(user_id: str, is_admin: bool = False) -> str:
    expire = datetime.utcnow() + timedelta(minutes=JWT_EXPIRE_MINUTES)
    return jwt.encode({"sub": user_id, "admin": is_admin, "exp": expire, "type": "access"}, JWT_SECRET, algorithm=JWT_ALGORITHM)

def create_refresh_token(user_id: str, family: str, expire_days: int = 7) -> str:
    expire = datetime.utcnow() + timedelta(days=expire_days)
    return jwt.encode({"sub": user_id, "family": family, "exp": expire, "type": "refresh"}, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=401, detail="token 无效或已过期")

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    payload = verify_token(credentials.credentials)
    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="非 access token")
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
