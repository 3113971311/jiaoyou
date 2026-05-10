from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import get_db
from models import User, RefreshToken
from schemas import *
from auth import create_access_token, create_refresh_token, verify_token, get_current_user
from utils.mailer import send_mail
from utils.card_code import generate_code, hash_text
import bcrypt, uuid, hashlib
from datetime import datetime, timedelta

router = APIRouter(tags=["auth"])

# 内存验证码存储 + 限流
codes_store = {}
rate_store = {}

@router.post("/auth/send-verify-code")
def send_verify_code(req: SendCodeRequest, db: Session = Depends(get_db)):
    # 业务校验
    if req.purpose == "register" and db.query(User).filter(User.email == req.email).first():
        raise HTTPException(400, "该邮箱已被注册")
    if req.purpose == "reset_password" and not db.query(User).filter(User.email == req.email).first():
        raise HTTPException(400, "该邮箱未注册")

    # 限流：60秒内不可重复发送
    rate_key = f"rate:{req.email}"
    now = datetime.utcnow()
    if rate_key in rate_store and rate_store[rate_key] > now:
        raise HTTPException(429, "验证码已发送，请60秒后再试")

    # 生成验证码
    key = f"{req.purpose}:{req.email}"
    code = f"{uuid.uuid4().int % 1000000:06d}"
    codes_store[key] = {"code": code, "expires": now + timedelta(minutes=5)}
    rate_store[rate_key] = now + timedelta(seconds=60)

    # 发送邮件
    from utils.mailer import send_mail as do_send
    try:
        do_send(req.email, f"验证码", f"您的验证码为：{code}，5分钟内有效。")
    except Exception as e:
        # 发送失败时清除验证码和限流，允许重试
        codes_store.pop(key, None)
        rate_store.pop(rate_key, None)
        raise HTTPException(500, f"邮件发送失败: {str(e).split(chr(10))[0]}")

    return {"message": "验证码已发送"}

@router.post("/auth/register")
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    key = f"register:{req.email}"
    stored = codes_store.get(key)
    if not stored or stored["code"] != req.code or stored["expires"] < datetime.utcnow():
        raise HTTPException(400, "验证码错误或已过期")
    if db.query(User).filter(User.username == req.username).first():
        raise HTTPException(400, "用户名已被注册")

    codes_store.pop(key, None)
    user = User(username=req.username, email=req.email, nickname=req.username,
                password_hash=bcrypt.hashpw(req.password.encode(), bcrypt.gensalt()).decode())
    db.add(user); db.commit()

    access = create_access_token(user.id, user.is_admin)
    refresh = create_refresh_token(user.id, str(uuid.uuid4()))
    db.add(RefreshToken(user_id=user.id, token_hash=hash_text(refresh), family="f", expires_at=datetime.utcnow()+timedelta(days=7)))
    db.commit()
    return {"access_token": access, "refresh_token": refresh}

@router.post("/auth/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter((User.username == req.account) | (User.email == req.account)).first()
    if not user or not bcrypt.checkpw(req.password.encode(), user.password_hash.encode()):
        raise HTTPException(401, "用户名或密码错误")
    if user.status in ("banned", "deleted"):
        raise HTTPException(403, "账号已封禁或删除")

    access = create_access_token(user.id, user.is_admin)
    refresh = create_refresh_token(user.id, str(uuid.uuid4()))
    db.add(RefreshToken(user_id=user.id, token_hash=hash_text(refresh), family="f", expires_at=datetime.utcnow()+timedelta(days=7)))
    db.commit()
    return {"access_token": access, "refresh_token": refresh}

@router.post("/auth/refresh")
def refresh_token(req: RefreshRequest, db: Session = Depends(get_db)):
    payload = verify_token(req.refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(401, "非 refresh token")
    hash_val = hash_text(req.refresh_token)
    stored = db.query(RefreshToken).filter(RefreshToken.token_hash == hash_val).first()
    if not stored or stored.revoked:
        raise HTTPException(401, "token 无效")
    stored.revoked = True
    user = db.query(User).filter(User.id == payload["sub"]).first()
    access = create_access_token(user.id, user.is_admin)
    refresh = create_refresh_token(user.id, payload.get("family", "f"))
    db.add(RefreshToken(user_id=user.id, token_hash=hash_text(refresh), family="f", expires_at=datetime.utcnow()+timedelta(days=7)))
    db.commit()
    return {"access_token": access, "refresh_token": refresh}

@router.get("/auth/me")
def get_me(user: User = Depends(get_current_user)):
    return {"id": user.id, "username": user.username, "email": user.email, "nickname": user.nickname,
            "avatar_url": user.avatar_url, "gender": user.gender, "bio": user.bio, "location": user.location,
            "vip_expires_at": user.vip_expires_at.isoformat() if user.vip_expires_at else None,
            "is_admin": user.is_admin, "status": user.status, "created_at": user.created_at.isoformat()}

@router.post("/auth/reset-password")
def reset_password(req: ResetPwdRequest, db: Session = Depends(get_db)):
    key = f"reset_password:{req.email}"
    stored = codes_store.get(key)
    if not stored or stored["code"] != req.code or stored["expires"] < datetime.utcnow():
        raise HTTPException(400, "验证码错误或已过期")
    user = db.query(User).filter(User.email == req.email).first()
    user.password_hash = bcrypt.hashpw(req.new_password.encode(), bcrypt.gensalt()).decode()
    db.commit(); codes_store.pop(key, None)
    return {"message": "密码已重置"}

@router.put("/auth/password")
def change_password(req: ChangePwdRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not bcrypt.checkpw(req.old_password.encode(), user.password_hash.encode()):
        raise HTTPException(400, "原密码错误")
    user.password_hash = bcrypt.hashpw(req.new_password.encode(), bcrypt.gensalt()).decode()
    db.commit()
    return {"message": "密码已修改"}
