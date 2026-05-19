import os
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, Form
from fastapi.responses import FileResponse
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from auth import get_admin_user, get_current_user, security
from config import UPLOAD_DIR
from database import get_db
from models import Notification, User
from utils.file_access import get_request_user, resolve_upload_path
from utils.uploads import IMAGE_EXTENSIONS, read_validated_upload

router = APIRouter(tags=["verify"])


@router.post("/verify/submit")
async def submit_verify(
    real_name: str = Form(""),
    id_card: str = Form(""),
    photo: UploadFile = File(None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user.verify_status == "pending":
        raise HTTPException(400, "已有审核中的认证申请")
    if user.is_verified:
        raise HTTPException(400, "已通过实名认证")
    if not real_name or not id_card:
        raise HTTPException(400, "请填写姓名和身份证号")
    if len(id_card) not in (15, 18):
        raise HTTPException(400, "身份证号格式不正确")

    id_photo_path = ""
    if photo and photo.filename:
        upload = await read_validated_upload(
            photo,
            max_bytes=10 * 1024 * 1024,
            allowed_kinds={"image"},
            allowed_extensions=IMAGE_EXTENSIONS,
            fallback_extension=".jpg",
            label="实名认证照片",
        )
        fname = f"verify_{uuid.uuid4()}{upload['ext']}"
        verify_dir = os.path.join(UPLOAD_DIR, "verify")
        os.makedirs(verify_dir, exist_ok=True)
        fpath = os.path.join(verify_dir, fname)
        with open(fpath, "wb") as f:
            f.write(upload["content"])
        id_photo_path = f"/verify/{fname}"

    user.real_name = real_name
    user.id_card = id_card
    user.id_photo = id_photo_path
    user.verify_status = "pending"
    db.commit()
    return {"message": "认证申请已提交，等待审核"}


@router.get("/verify/status")
def verify_status(user: User = Depends(get_current_user)):
    return {
        "verified": user.is_verified,
        "status": user.verify_status,
        "real_name": user.real_name,
        "id_card": user.id_card[:6] + "********" + user.id_card[-4:] if user.id_card else "",
    }


@router.get("/admin/verifications")
def list_verifications(
    status: str = "",
    page: int = 1,
    limit: int = 20,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    q = db.query(User).filter(User.verify_status != "")
    if status:
        q = q.filter(User.verify_status == status)
    total = q.count()
    items = q.order_by(User.updated_at.desc()).offset((page - 1) * limit).limit(limit).all()
    return {
        "items": [
            {
                "id": u.id,
                "username": u.username,
                "nickname": u.nickname,
                "avatar_url": u.avatar_url,
                "real_name": u.real_name,
                "id_card": u.id_card or "",
                "id_photo": u.id_photo,
                "verify_status": u.verify_status,
                "is_verified": u.is_verified,
            }
            for u in items
        ],
        "total": total,
    }


@router.post("/admin/verifications/{user_id}/review")
def review_verification(
    user_id: str,
    req: dict,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        raise HTTPException(404)
    action = req.get("action", "")
    if action not in ("approve", "reject"):
        raise HTTPException(400, "action 必须是 approve 或 reject")

    if action == "approve":
        u.verify_status = "approved"
        u.is_verified = True
        db.add(Notification(user_id=u.id, type="verify_approved", title="实名认证通过", content="您的实名认证已通过审核"))
    else:
        reason = req.get("comment", "")
        u.verify_status = "rejected"
        u.is_verified = False
        u.real_name = ""
        u.id_card = ""
        if u.id_photo:
            fpath = resolve_upload_path(u.id_photo, allowed_prefixes=("verify",))
            if fpath.exists():
                os.remove(fpath)
            u.id_photo = ""
        db.add(Notification(user_id=u.id, type="verify_rejected", title="实名认证未通过", content=reason or "您的实名认证未通过审核"))

    db.commit()
    return {"message": "已审核"}


@router.post("/admin/verifications/{user_id}/reset")
def reset_verification(
    user_id: str,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        raise HTTPException(404)
    if u.id_photo:
        fpath = resolve_upload_path(u.id_photo, allowed_prefixes=("verify",))
        if fpath.exists():
            os.remove(fpath)
    u.verify_status = ""
    u.is_verified = False
    u.real_name = ""
    u.id_card = ""
    u.id_photo = ""
    db.commit()
    return {"message": "已重置"}


@router.get("/verify/photo")
def get_verify_photo(
    request: Request,
    path: str = "",
    token: str = "",
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db),
):
    user = get_request_user(request, db, credentials=credentials, query_token=token)
    if not user.is_admin:
        raise HTTPException(403)
    full_path = resolve_upload_path(path, allowed_prefixes=("verify",))
    if not full_path.exists():
        raise HTTPException(404)
    return FileResponse(full_path)
