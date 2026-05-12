from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from database import get_db
from models import User, Notification
from auth import get_current_user, get_admin_user, verify_token
from config import UPLOAD_DIR
import os, uuid

router = APIRouter(tags=["verify"])

@router.post("/verify/submit")
async def submit_verify(
    real_name: str = Form(""),
    id_card: str = Form(""),
    photo: UploadFile = File(None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """用户提交实名认证：姓名 + 身份证号 + 手持身份证照片"""
    if user.verify_status == "pending":
        raise HTTPException(400, "已有审核中的认证申请")
    if user.is_verified:
        raise HTTPException(400, "已通过实名认证")

    if not real_name or not id_card:
        raise HTTPException(400, "请填写姓名和身份证号")
    if len(id_card) not in (15, 18):
        raise HTTPException(400, "身份证号格式不正确")

    # 保存照片
    id_photo_path = ""
    if photo and photo.filename:
        ext = os.path.splitext(photo.filename)[1] or ".jpg"
        fname = f"verify_{uuid.uuid4()}{ext}"
        verify_dir = os.path.join(UPLOAD_DIR, "verify")
        os.makedirs(verify_dir, exist_ok=True)
        fpath = os.path.join(verify_dir, fname)
        content = await photo.read()
        with open(fpath, "wb") as f:
            f.write(content)
        id_photo_path = f"/verify/{fname}"

    user.real_name = real_name
    user.id_card = id_card
    user.id_photo = id_photo_path
    user.verify_status = "pending"
    db.commit()
    return {"message": "认证申请已提交，等待审核"}


@router.get("/verify/status")
def verify_status(user: User = Depends(get_current_user)):
    """查询当前用户的实名认证状态"""
    return {
        "verified": user.is_verified,
        "status": user.verify_status,
        "real_name": user.real_name,
        "id_card": user.id_card[:6] + "********" + user.id_card[-4:] if user.id_card else "",
    }


# ─── Admin 实名审核 ───

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
    """审核实名认证：通过或拒绝"""
    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        raise HTTPException(404)
    action = req.get("action", "")
    if action not in ("approve", "reject"):
        raise HTTPException(400, "action 必须为 approve 或 reject")

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
            fpath = os.path.join(UPLOAD_DIR, u.id_photo.lstrip("/"))
            if os.path.exists(fpath):
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
    """重置用户的实名认证信息（管理员删除已通过的认证）"""
    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        raise HTTPException(404)
    if u.id_photo:
        fpath = os.path.join(UPLOAD_DIR, u.id_photo.lstrip("/"))
        if os.path.exists(fpath):
            os.remove(fpath)
    u.verify_status = ""
    u.is_verified = False
    u.real_name = ""
    u.id_card = ""
    u.id_photo = ""
    db.commit()
    return {"message": "已重置"}

# 审核中查看身份证照片（token 鉴权）
@router.get("/verify/photo")
def get_verify_photo(
    path: str = "",
    token: str = "",
    db: Session = Depends(get_db),
):
    try:
        payload = verify_token(token)
        user = db.query(User).filter(User.id == payload["sub"]).first()
        if not user or not user.is_admin:
            raise HTTPException(403)
    except:
        raise HTTPException(401)
    safe = path.replace("\\", "/").replace("..", "")
    full_path = os.path.join(UPLOAD_DIR, safe.lstrip("/"))
    if not os.path.exists(full_path):
        raise HTTPException(404)
    return FileResponse(full_path)
