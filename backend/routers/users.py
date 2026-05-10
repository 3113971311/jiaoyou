from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy.orm import Session
from database import get_db
from models import User, ReviewQueue
from schemas import *
from auth import get_current_user, get_admin_user
import bcrypt, os, uuid
from config import UPLOAD_DIR

router = APIRouter(tags=["users"])

@router.get("/users/{user_id}")
def get_user(user_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    u = db.query(User).filter(User.id == user_id).first()
    if not u or u.status == "banned":
        raise HTTPException(404, "用户不存在")
    return {"id": u.id, "username": u.username, "nickname": u.nickname, "avatar_url": u.avatar_url,
            "gender": u.gender, "bio": u.bio, "location": u.location,
            "vip_expires_at": u.vip_expires_at.isoformat() if u.vip_expires_at else None,
            "created_at": u.created_at.isoformat(), "status": u.status}

@router.put("/users/profile")
def update_profile(req: UpdateProfileRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    for k, v in req.dict(exclude_unset=True).items():
        if v is not None: setattr(user, k, v)
    db.commit()
    return {"message": "已更新"}

@router.post("/users/avatar")
async def upload_avatar(file: UploadFile, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ext = os.path.splitext(file.filename)[1] or ".jpg"
    fname = f"{uuid.uuid4()}{ext}"
    staging_dir = os.path.join(UPLOAD_DIR, "staging", "avatar")
    os.makedirs(staging_dir, exist_ok=True)
    fpath = os.path.join(staging_dir, fname)
    content = await file.read()
    with open(fpath, "wb") as f: f.write(content)
    rel_path = f"/staging/avatar/{fname}"
    user.avatar_staging = rel_path; db.commit()
    db.add(ReviewQueue(image_url=rel_path, image_type="avatar", related_id=user.id, submitted_by=user.id))
    db.commit()
    return {"message": "头像已上传，等待审核", "staging_url": rel_path}

# Admin routes
@router.get("/admin/users")
def admin_list_users(search: str = "", status: str = "", page: int = 1, limit: int = 20,
                     admin: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    q = db.query(User)
    if search: q = q.filter((User.username.contains(search)) | (User.email.contains(search)) | (User.nickname.contains(search)))
    if status and status != "all": q = q.filter(User.status == status)
    elif not status: q = q.filter(User.status != "deleted")
    total = q.count()
    items = q.order_by(User.created_at.desc()).offset((page-1)*limit).limit(limit).all()
    return {"items": [{"id": u.id, "username": u.username, "email": u.email, "nickname": u.nickname,
            "gender": u.gender, "location": u.location, "vip_expires_at": u.vip_expires_at.isoformat() if u.vip_expires_at else None,
            "is_admin": u.is_admin, "status": u.status, "warning_count": u.warning_count, "created_at": u.created_at.isoformat()} for u in items], "total": total}

@router.post("/admin/users")
def admin_create_user(req: CreateUserRequest, admin: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    if db.query(User).filter((User.username == req.username) | (User.email == req.email)).first():
        raise HTTPException(400, "用户名或邮箱已存在")
    u = User(username=req.username, email=req.email, nickname=req.nickname or req.username, gender=req.gender,
             is_admin=req.is_admin, password_hash=bcrypt.hashpw(req.password.encode(), bcrypt.gensalt()).decode(),
             vip_expires_at=None)
    if req.vip_days > 0:
        from datetime import datetime, timedelta
        u.vip_expires_at = datetime.utcnow() + timedelta(days=req.vip_days)
    db.add(u); db.commit()
    return {"id": u.id, "username": u.username}

@router.put("/admin/users/{user_id}")
def admin_update_user(user_id: str, req: UpdateUserRequest, admin: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    u = db.query(User).filter(User.id == user_id).first()
    if not u: raise HTTPException(404)
    for k, v in req.dict(exclude_unset=True).items():
        if v is not None:
            if k == "password":
                v = bcrypt.hashpw(v.encode(), bcrypt.gensalt()).decode()
                k = "password_hash"
            if k == "vip_expires_at":
                from datetime import datetime
                v = datetime.fromisoformat(v.replace("Z", "+00:00")) if v else None
            setattr(u, k, v)
    db.commit(); return {"id": u.id, "username": u.username}

@router.put("/admin/users/{user_id}/status")
def admin_toggle_status(user_id: str, req: dict, admin: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    u = db.query(User).filter(User.id == user_id).first()
    if not u: raise HTTPException(404)
    if u.is_admin and req.get("status") == "banned": raise HTTPException(400, "不能封禁管理员账号")
    u.status = req.get("status", u.status); db.commit()
    return {"message": "已更新"}

@router.post("/admin/users/{user_id}/remove-vip")
def admin_remove_vip(user_id: str, admin: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    u = db.query(User).filter(User.id == user_id).first()
    u.vip_expires_at = None; db.commit()
    return {"message": "VIP已移除"}

@router.delete("/admin/users/{user_id}")
def admin_delete_user(user_id: str, admin: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    target = db.query(User).filter(User.id == user_id).first()
    if not target: raise HTTPException(404)
    if target.is_admin: raise HTTPException(400, "不能删除管理员账号")
    if target.id == admin.id: raise HTTPException(400, "不能删除自己的账号")
    target.status = "deleted"
    db.commit()
    return {"message": "已删除"}

@router.delete("/admin/users/{user_id}/permanent")
def admin_permanent_delete(user_id: str, admin: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    target = db.query(User).filter(User.id == user_id).first()
    if not target: raise HTTPException(404)
    if target.is_admin: raise HTTPException(400, "不能删除管理员账号")
    if target.id == admin.id: raise HTTPException(400, "不能删除自己的账号")
    db.delete(target)
    db.commit()
    return {"message": "已永久删除"}
