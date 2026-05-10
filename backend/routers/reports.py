from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Report, Warning, Blacklist, Follow, Notification, User
from schemas import SubmitReportRequest, WarnUserRequest
from auth import get_current_user, get_vip_user, get_admin_user
from datetime import datetime

router = APIRouter(tags=["reports"])

@router.post("/reports")
def submit_report(req: SubmitReportRequest, user: User = Depends(get_vip_user), db: Session = Depends(get_db)):
    db.add(Report(reporter_id=user.id, target_type=req.target_type, target_id=req.target_id, reason=req.reason))
    db.commit()
    return {"message": "举报已提交"}

@router.get("/admin/reports")
def admin_reports(status: str = "", page: int = 1, limit: int = 20, admin: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    q = db.query(Report)
    if status: q = q.filter(Report.status == status)
    total = q.count()
    items = q.order_by(Report.created_at.desc()).offset((page-1)*limit).limit(limit).all()
    return {"items": [{"id": i.id, "reporter_id": i.reporter_id, "target_type": i.target_type, "target_id": i.target_id, "reason": i.reason, "status": i.status} for i in items], "total": total}

@router.post("/admin/reports/{report_id}/handle")
def handle_report(report_id: str, req: dict, admin: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    r = db.query(Report).filter(Report.id == report_id).first()
    if not r: raise HTTPException(404)
    r.status = "handled" if req.get("action") != "dismiss" else "dismissed"
    r.handled_by = admin.id; r.result = req.get("result", ""); r.handled_at = datetime.utcnow()
    db.commit()
    return {"message": "已处理"}

@router.post("/admin/users/{user_id}/warn")
def warn_user(user_id: str, req: WarnUserRequest, admin: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    db.add(Warning(user_id=user_id, warned_by=admin.id, reason=req.reason, related_chat_image_url=req.related_chat_image_url))
    count = db.query(Warning).filter(Warning.user_id == user_id).count()
    db.add(Notification(user_id=user_id, type="warning", title="收到警告", content=req.reason))
    if count >= 3:
        db.query(User).filter(User.id == user_id).update({"status": "banned"})
        db.add(Notification(user_id=user_id, type="banned", title="账号已封禁", content="累计3次警告，账号已被封禁"))
    db.commit()
    return {"warning_count": count, "banned": count >= 3}

@router.get("/admin/users/{user_id}/warnings")
def user_warnings(user_id: str, admin: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    return db.query(Warning).filter(Warning.user_id == user_id).order_by(Warning.created_at.desc()).all()

@router.post("/blacklist/{target_id}")
def block_user(target_id: str, user: User = Depends(get_vip_user), db: Session = Depends(get_db)):
    if db.query(Blacklist).filter(Blacklist.blocker_id == user.id, Blacklist.blocked_id == target_id).first():
        raise HTTPException(400, "已拉黑")
    db.query(Follow).filter((Follow.follower_id == user.id) & (Follow.followed_id == target_id) | (Follow.follower_id == target_id) & (Follow.followed_id == user.id)).delete()
    db.add(Blacklist(blocker_id=user.id, blocked_id=target_id))
    db.commit()
    return {"message": "已拉黑"}

@router.delete("/blacklist/{target_id}")
def unblock_user(target_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db.query(Blacklist).filter(Blacklist.blocker_id == user.id, Blacklist.blocked_id == target_id).delete()
    db.commit()
    return {"message": "已解除"}

@router.get("/blacklist")
def my_blacklist(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    items = db.query(Blacklist).filter(Blacklist.blocker_id == user.id).all()
    blocked_users = db.query(User).filter(User.id.in_([i.blocked_id for i in items])).all()
    return [{"id": u.id, "username": u.username, "nickname": u.nickname} for u in blocked_users]
