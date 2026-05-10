from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import Notification, User
from auth import get_current_user

router = APIRouter(tags=["notifications"])

@router.get("/notifications")
def list_notifs(cursor: str = "", limit: int = 30, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    q = db.query(Notification).filter(Notification.user_id == user.id).order_by(Notification.created_at.desc())
    if cursor: q = q.filter(Notification.id < cursor)
    items = q.limit(limit + 1).all()
    unread = db.query(Notification).filter(Notification.user_id == user.id, Notification.is_read == False).count()
    return {"items": [{"id": i.id, "type": i.type, "title": i.title, "content": i.content, "is_read": i.is_read, "created_at": i.created_at.isoformat()} for i in items[:limit]],
            "unread_count": unread, "next_cursor": items[limit-1].id if len(items) > limit else None}

@router.put("/notifications/{notif_id}/read")
def mark_read(notif_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db.query(Notification).filter(Notification.id == notif_id, Notification.user_id == user.id).update({"is_read": True})
    db.commit()
    return {"message": "已读"}

@router.put("/notifications/read-all")
def mark_all_read(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db.query(Notification).filter(Notification.user_id == user.id, Notification.is_read == False).update({"is_read": True})
    db.commit()
    return {"message": "全部已读"}
