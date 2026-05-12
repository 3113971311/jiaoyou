from fastapi import APIRouter, Depends, HTTPException, Request
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
        r = requests.get(f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lng}&zoom=18&accept-language=zh",
                        headers={"User-Agent": "FriendChat/1.0"}, timeout=5)
        if r.ok:
            addr = r.json().get("address", {})
            # 精确到区/县
            district = addr.get("district") or addr.get("county") or addr.get("city_district") or addr.get("suburb") or ""
            city = addr.get("city") or addr.get("town") or ""
            province = addr.get("state") or addr.get("province") or ""
            # 组装完整地址
            parts = [p for p in [province, city, district] if p]
            location_str = ", ".join(parts) if parts else ""
            # 省简称用于匹配
            province_short = province.replace("省","").replace("市","").strip() if province else ""
            city_short = city.replace("市","").strip() if city else ""
            return location_str, province_short, district
    except: pass
    return "", "", ""

@router.post("/match/start")
def start_match(req: StartMatchRequest, user: User = Depends(get_vip_user), db: Session = Depends(get_db)):
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    dc = db.query(MatchDailyCount).filter(MatchDailyCount.user_id == user.id, MatchDailyCount.date >= today).first()
    if dc and dc.count >= 5:
        raise HTTPException(400, "今日匹配次数已用完（5次/天）")

    existing = db.query(MatchQueue).filter(MatchQueue.user_id == user.id, MatchQueue.status == "waiting", MatchQueue.expires_at > datetime.utcnow()).first()
    if existing: raise HTTPException(400, "你已在匹配队列中")

    location_str, province, district = reverse_geocode(req.latitude, req.longitude)
    if location_str:
        user.location = location_str
        db.commit()

    prefer = req.prefer_gender or ("male" if user.gender == "female" else "female")
    expires = datetime.utcnow() + timedelta(hours=12)
    me = MatchQueue(user_id=user.id, scope=req.scope, city=district or location_str, province=province,
                    latitude=req.latitude, longitude=req.longitude, prefer_gender=prefer, expires_at=expires)
    db.add(me); db.flush()

    # 尝试匹配
    candidates = db.query(MatchQueue).filter(
        MatchQueue.user_id != user.id, MatchQueue.status == "waiting",
        MatchQueue.expires_at > datetime.utcnow(),
        MatchQueue.prefer_gender == (user.gender or "male")
    ).order_by(MatchQueue.created_at.asc()).all()

    for c in candidates:
        if c.scope == req.scope and ((req.scope == "city" and c.city == district) or (req.scope == "province" and c.province == province)):
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

@router.get("/geocode/search")
def geocode_search(q: str = ""):
    """根据地点名称查询经纬度"""
    if not q: return {"lat": None, "lng": None}
    try:
        import requests
        r = requests.get("https://nominatim.openstreetmap.org/search", params={
            "q": q, "format": "json", "limit": 1, "accept-language": "zh",
        }, headers={"User-Agent": "FriendChat/1.0"}, timeout=5)
        if r.ok and r.json():
            data = r.json()[0]
            return {"lat": float(data["lat"]), "lng": float(data["lon"])}
    except: pass
    return {"lat": None, "lng": None}

@router.get("/geocode/reverse")
def geocode_reverse(lat: float = 0, lng: float = 0):
    """根据经纬度反查地址（免登录）"""
    if not lat or not lng: return {"location": ""}
    try:
        import requests
        r = requests.get(f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lng}&zoom=18&accept-language=zh",
                        headers={"User-Agent": "FriendChat/1.0"}, timeout=5)
        if r.ok:
            addr = r.json().get("address", {})
            district = addr.get("district") or addr.get("county") or addr.get("city_district") or addr.get("suburb") or ""
            city = addr.get("city") or addr.get("town") or ""
            province = addr.get("state") or addr.get("province") or ""
            parts = [p for p in [province, city, district] if p]
            return {"location": ", ".join(parts) if parts else ""}
    except: pass
    return {"location": ""}

@router.get("/geocode/ip-locate")
def ip_locate(ip: str = ""):
    """根据指定IP获取经纬度和地址（用于WebRTC获取的真实IP）"""
    if not ip: return {"lat": None, "lng": None, "location": ""}
    try:
        import requests
        r = requests.get(f"https://ipapi.co/{ip}/json/", timeout=5)
        if r.ok:
            d = r.json()
            if d.get("latitude") and d.get("longitude"):
                parts = [p for p in [d.get("region"), d.get("city")] if p]
                return {"lat": float(d["latitude"]), "lng": float(d["longitude"]),
                        "location": ", ".join(parts) if parts else ""}
    except: pass
    return {"lat": None, "lng": None, "location": ""}

@router.get("/geocode/my-ip")
def my_ip_locate(request: Request):
    """根据请求来源IP获取经纬度和地址（服务端视角，不受浏览器代理影响？会受影响）"""
    client_ip = request.client.host if request.client else ""
    if not client_ip or client_ip in ("127.0.0.1", "::1", "localhost"):
        return {"lat": None, "lng": None, "location": "本地环境无法获取IP"}
    try:
        import requests
        r = requests.get(f"https://ipapi.co/{client_ip}/json/", timeout=5)
        if r.ok:
            d = r.json()
            if d.get("latitude") and d.get("longitude"):
                parts = [p for p in [d.get("region"), d.get("city")] if p]
                return {"lat": float(d["latitude"]), "lng": float(d["longitude"]),
                        "location": ", ".join(parts) if parts else ""}
    except: pass
    return {"lat": None, "lng": None, "location": ""}

@router.get("/match/history")
def match_history(page: int = 1, limit: int = 10, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    items = db.query(MatchQueue).filter(MatchQueue.user_id == user.id).order_by(MatchQueue.created_at.desc()).offset((page-1)*limit).limit(limit).all()
    return {"items": [{"id": i.id, "status": i.status, "scope": i.scope, "matched_at": i.matched_at.isoformat() if i.matched_at else None} for i in items]}
