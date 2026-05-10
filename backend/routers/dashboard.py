from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import User, MatchQueue, Moment, ReviewQueue, Report
from auth import get_admin_user
from datetime import datetime, timedelta

router = APIRouter(tags=["dashboard"])

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
