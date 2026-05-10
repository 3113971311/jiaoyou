from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import MatchQueue, MatchDailyCount, User, Conversation, Message, Notification
from schemas import StartMatchRequest
from auth import get_current_user, get_vip_user
from datetime import datetime, timedelta
import httpx

router = APIRouter(tags=["match"])

def reverse_geocode(lat: float, lng: float):
    try:
        import requests
        r = requests.get(f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lng}&zoom=10&accept-language=zh",
                        headers={"User-Agent": "FriendChat/1.0"}, timeout=5)
        if r.ok:
            addr = r.json().get("address", {})
            return addr.get("city") or addr.get("town") or "", addr.get("state") or addr.get("province") or ""
    except: pass
    return "", ""

@router.post("/match/start")
def start_match(req: StartMatchRequest, user: User = Depends(get_vip_user), db: Session = Depends(get_db)):
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    dc = db.query(MatchDailyCount).filter(MatchDailyCount.user_id == user.id, MatchDailyCount.date >= today).first()
    if dc and dc.count >= 5:
        raise HTTPException(400, "今日匹配次数已用完（5次/天）")

    existing = db.query(MatchQueue).filter(MatchQueue.user_id == user.id, MatchQueue.status == "waiting", MatchQueue.expires_at > datetime.utcnow()).first()
    if existing: raise HTTPException(400, "你已在匹配队列中")

    city, province = reverse_geocode(req.latitude, req.longitude)
    if city or province:
        user.location = f"{city}, {province}" if city else province
        db.commit()

    prefer = req.prefer_gender or ("male" if user.gender == "female" else "female")
    expires = datetime.utcnow() + timedelta(hours=12)
    me = MatchQueue(user_id=user.id, scope=req.scope, city=city, province=province,
                    latitude=req.latitude, longitude=req.longitude, prefer_gender=prefer, expires_at=expires)
    db.add(me); db.flush()

    # 尝试匹配
    candidates = db.query(MatchQueue).filter(
        MatchQueue.user_id != user.id, MatchQueue.status == "waiting",
        MatchQueue.expires_at > datetime.utcnow(),
        MatchQueue.prefer_gender == (user.gender or "male")
    ).order_by(MatchQueue.created_at.asc()).all()

    for c in candidates:
        if c.scope == req.scope and ((req.scope == "city" and c.city == city) or (req.scope == "province" and c.province == province)):
            a, b = sorted([user.id, c.user_id])
            conv = Conversation(user1_id=a, user2_id=b, last_message_at=datetime.utcnow())
            db.add(conv); db.flush()
            me.status = "matched"; me.matched_with = c.user_id; me.matched_at = datetime.utcnow()
            c.status = "matched"; c.matched_with = user.id; c.matched_at = datetime.utcnow()
            db.add(Message(conversation_id=conv.id, sender_id=user.id, content="你们配对成功，开始聊天吧！"))
            for uid in [user.id, c.user_id]:
                db.add(Notification(user_id=uid, type="match_success", title="配对成功", content="你们配对成功，开始聊天吧！"))

            if not dc: dc = MatchDailyCount(user_id=user.id, date=today, count=1); db.add(dc)
            else: dc.count += 1
            db.commit()
            return {"matched": True, "conversation_id": conv.id, "matched_user": {"id": c.user_id}}

    db.commit()
    return {"message": "已进入匹配队列", "queue_id": me.id}

@router.post("/match/cancel")
def cancel_match(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db.query(MatchQueue).filter(MatchQueue.user_id == user.id, MatchQueue.status == "waiting").update({"status": "cancelled"})
    db.commit()
    return {"message": "已取消"}

@router.get("/match/status")
def match_status(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    active = db.query(MatchQueue).filter(
        MatchQueue.user_id == user.id,
        MatchQueue.status.in_(["waiting", "matched"]),
    ).order_by(MatchQueue.created_at.desc()).first()
    if active and active.status == "waiting" and active.expires_at < datetime.utcnow():
        active.status = "expired"; db.commit(); active = None
    if not active:
        return {"is_matching": False, "is_matched": False, "matched_user": None}
    matched_user = None
    if active.matched_with:
        mu = db.query(User).filter(User.id == active.matched_with).first()
        if mu: matched_user = {"id": mu.id, "username": mu.username, "nickname": mu.nickname, "avatar_url": mu.avatar_url}
    return {"is_matching": active.status == "waiting", "is_matched": active.status == "matched",
            "matched_user": matched_user, "expires_at": active.expires_at.isoformat() if active.expires_at else None}

@router.get("/match/history")
def match_history(page: int = 1, limit: int = 10, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    items = db.query(MatchQueue).filter(MatchQueue.user_id == user.id).order_by(MatchQueue.created_at.desc()).offset((page-1)*limit).limit(limit).all()
    return {"items": [{"id": i.id, "status": i.status, "scope": i.scope, "matched_at": i.matched_at.isoformat() if i.matched_at else None} for i in items]}
