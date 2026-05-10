from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import User, MatchQueue, Moment, ReviewQueue, Report
from auth import get_admin_user
from datetime import datetime, timedelta

router = APIRouter(tags=["dashboard"])

STAT_MAP = {
    "total_users": User,
    "active_vip": User,
    "banned_users": User,
    "today_new_users": User,
    "pending_reviews": ReviewQueue,
    "pending_reports": Report,
}

@router.get("/admin/dashboard")
def dashboard(admin: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    now = datetime.utcnow()
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)

    return {
        "total_users": db.query(User).filter(User.status != "deleted").count(),
        "today_new_users": db.query(User).filter(User.created_at >= today, User.status != "deleted").count(),
        "active_vip": db.query(User).filter(User.vip_expires_at > now).count(),
        "today_matches": db.query(MatchQueue).filter(MatchQueue.status == "matched", MatchQueue.matched_at >= today).count(),
        "pending_reviews": db.query(ReviewQueue).filter(ReviewQueue.status == "pending").count(),
        "today_moments": db.query(Moment).filter(Moment.created_at >= today).count(),
        "pending_reports": db.query(Report).filter(Report.status == "pending").count(),
        "banned_users": db.query(User).filter(User.status == "banned").count(),
        "latest_moments": [{"id": m.id, "text": (m.content_text or "(图片)")[:60], "user": m.user.nickname or m.user.username, "time": m.created_at.isoformat()}
                           for m in db.query(Moment).filter(Moment.status == "approved").order_by(Moment.created_at.desc()).limit(5).all()],
        "latest_matches": [{"id": m.id, "user1": "", "user2": "", "scope": m.scope, "time": m.matched_at.isoformat() if m.matched_at else ""}
                           for m in db.query(MatchQueue).filter(MatchQueue.status == "matched").order_by(MatchQueue.matched_at.desc()).limit(5).all()],
        "latest_users": [{"id": u.id, "username": u.username, "nickname": u.nickname, "time": u.created_at.isoformat()}
                         for u in db.query(User).filter(User.status != "deleted").order_by(User.created_at.desc()).limit(5).all()],
    }

@router.get("/admin/dashboard/detail")
def dashboard_detail(type: str, page: int = 1, limit: int = 20,
                     admin: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    now = datetime.utcnow()
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    items = []
    total = 0

    if type == "total_users":
        q = db.query(User).filter(User.status != "deleted").order_by(User.created_at.desc())
        total = q.count()
        rows = q.offset((page-1)*limit).limit(limit).all()
        items = [{"id": u.id, "c1": u.username, "c2": u.email, "c3": u.nickname or "-", "c4": "管理员" if u.is_admin else ("VIP" if (u.vip_expires_at and u.vip_expires_at > now) else "普通"), "c5": u.created_at.isoformat()[:10]} for u in rows]

    elif type == "today_new_users":
        q = db.query(User).filter(User.created_at >= today, User.status != "deleted").order_by(User.created_at.desc())
        total = q.count()
        rows = q.offset((page-1)*limit).limit(limit).all()
        items = [{"id": u.id, "c1": u.username, "c2": u.email, "c3": u.nickname or "-", "c4": u.created_at.isoformat()[:10]} for u in rows]

    elif type == "active_vip":
        q = db.query(User).filter(User.vip_expires_at > now).order_by(User.vip_expires_at.desc())
        total = q.count()
        rows = q.offset((page-1)*limit).limit(limit).all()
        items = [{"id": u.id, "c1": u.username, "c2": u.nickname or "-", "c3": u.vip_expires_at.isoformat()[:10] if u.vip_expires_at else "-", "c4": f"剩余{(u.vip_expires_at - now).days}天"} for u in rows]

    elif type == "banned_users":
        q = db.query(User).filter(User.status == "banned").order_by(User.created_at.desc())
        total = q.count()
        rows = q.offset((page-1)*limit).limit(limit).all()
        items = [{"id": u.id, "c1": u.username, "c2": u.email, "c3": u.nickname or "-", "c4": u.created_at.isoformat()[:10]} for u in rows]

    elif type == "pending_reviews":
        q = db.query(ReviewQueue).filter(ReviewQueue.status == "pending").order_by(ReviewQueue.submitted_at.desc())
        total = q.count()
        rows = q.offset((page-1)*limit).limit(limit).all()
        items = [{"id": r.id, "c1": r.image_type, "c2": r.image_url or "-", "c3": r.submitted_at.isoformat()[:19] if r.submitted_at else "-"} for r in rows]

    elif type == "pending_reports":
        q = db.query(Report).filter(Report.status == "pending").order_by(Report.created_at.desc())
        total = q.count()
        rows = q.offset((page-1)*limit).limit(limit).all()
        items = [{"id": r.id, "c1": r.target_type, "c2": r.target_id, "c3": r.reason[:60] if r.reason else "-", "c4": r.created_at.isoformat()[:19] if r.created_at else "-"} for r in rows]

    elif type == "today_matches":
        q = db.query(MatchQueue).filter(MatchQueue.status == "matched", MatchQueue.matched_at >= today).order_by(MatchQueue.matched_at.desc())
        total = q.count()
        rows = q.offset((page-1)*limit).limit(limit).all()
        items = [{"id": m.id, "c1": m.user1_id, "c2": m.user2_id, "c3": m.scope or "-", "c4": m.matched_at.isoformat()[:19] if m.matched_at else "-"} for m in rows]

    elif type == "today_moments":
        q = db.query(Moment).filter(Moment.created_at >= today).order_by(Moment.created_at.desc())
        total = q.count()
        rows = q.offset((page-1)*limit).limit(limit).all()
        items = [{"id": m.id, "c1": (m.user.nickname or m.user.username) if m.user else "-", "c2": (m.content_text or "(图片)")[:80], "c3": m.created_at.isoformat()[:19] if m.created_at else "-"} for m in rows]

    else:
        raise HTTPException(400, "未知类型")

    return {"items": items, "total": total}
