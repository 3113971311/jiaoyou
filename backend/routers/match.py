from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from database import get_db
from models import MatchQueue, MatchDailyCount, User, Conversation, Message, Notification, SiteConfig
from schemas import StartMatchRequest
from auth import get_current_user, get_vip_user, get_admin_user
from datetime import datetime, timedelta

router = APIRouter(tags=["match"])

def get_amap_key(db: Session):
    cfg = db.query(SiteConfig).filter(SiteConfig.config_key == "amap_key").first()
    return cfg.config_value if cfg and cfg.config_value else ""

def reverse_geocode(lat: float, lng: float):
    """高德逆地理编码"""
    try:
        import requests
        from database import get_db
        db = next(get_db())
        key = get_amap_key(db)
        db.close()
        if not key: return "", "", ""
        r = requests.get("https://restapi.amap.com/v3/geocode/regeo",
                         params={"key": key, "location": f"{lng},{lat}", "extensions": "base"},
                         timeout=5)
        if r.ok:
            data = r.json()
            if data.get("status") == "1":
                comp = data.get("regeocode", {}).get("addressComponent", {})
                province = comp.get("province", "")
                city = comp.get("city", "") or province
                district = comp.get("district", "")
                # 短名称
                province_short = province.replace("省", "").replace("市", "").strip() if province else ""
                city_short = city.replace("市", "").strip() if city else ""
                parts = [p for p in [province, city, district] if p and p]
                location_str = ", ".join(parts) if parts else ""
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
def geocode_reverse(lat: float = 0, lng: float = 0, db: Session = Depends(get_db)):
    """高德逆地理编码（免登录）"""
    if not lat or not lng: return {"location": ""}
    key = get_amap_key(db)
    if not key: return {"location": ""}
    try:
        import requests
        r = requests.get("https://restapi.amap.com/v3/geocode/regeo",
                         params={"key": key, "location": f"{lng},{lat}", "extensions": "base"},
                         timeout=5)
        if r.ok and r.json().get("status") == "1":
            comp = r.json().get("regeocode", {}).get("addressComponent", {})
            parts = [p for p in [comp.get("province", ""), comp.get("city", "") or comp.get("province", ""), comp.get("district", "")] if p]
            return {"location": ", ".join(parts) if parts else ""}
    except: pass
    return {"location": ""}

@router.get("/geocode/ip-locate")
def ip_locate(ip: str = ""):
    """根据指定IP获取经纬度和地址（用于WebRTC获取的真实IP）"""
    if not ip: return {"lat": None, "lng": None, "location": ""}
    try:
        import requests
        r = requests.get(f"http://ip-api.com/json/{ip}?fields=status,lat,lon,city,regionName,country", timeout=5)
        if r.ok:
            d = r.json()
            if d.get("status") == "success":
                parts = [p for p in [d.get("regionName"), d.get("city")] if p]
                return {"lat": float(d["lat"]), "lng": float(d["lon"]),
                        "location": ", ".join(parts) if parts else ""}
    except: pass
    return {"lat": None, "lng": None, "location": ""}

@router.get("/geocode/my-ip")
def my_ip_locate(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """高德IP定位，返回中文省市区。普通用户每天限1次，管理员无限制。"""
    # 每日限制检查（管理员跳过）
    if not user.is_admin and user.last_located_at:
        elapsed = datetime.utcnow() - user.last_located_at
        if elapsed < timedelta(hours=24):
            return {"lat": None, "lng": None, "location": "", "limited": True,
                    "msg": f"每天只能更新一次定位，请{24 - int(elapsed.total_seconds()//3600)}小时后再试"}
    key = get_amap_key(db)
    if not key: return {"lat": None, "lng": None, "location": "未配置高德Key"}
    try:
        import requests
        r = requests.get("https://restapi.amap.com/v3/ip", params={"key": key}, timeout=8)
        if r.ok:
            d = r.json()
            if d.get("status") == "1":
                adcode = d.get("adcode", "")
                province = d.get("province", "")
                city = d.get("city", "")
                # 用adcode反查区县
                district = ""
                if adcode:
                    try:
                        r2 = requests.get("https://restapi.amap.com/v3/config/district",
                                         params={"key": key, "keywords": "" if len(adcode) < 4 else adcode[:4], "subdistrict": 1},
                                         timeout=5)
                        if r2.ok:
                            d2 = r2.json()
                            districts = d2.get("districts", [])
                            if districts and districts[0].get("districts"):
                                district = districts[0]["districts"][0]["name"]
                    except: pass
                parts = [p for p in [province, city, district] if p and p]
                # 尝试从高德逆地理编码获取精确位置
                rect = d.get("rectangle", "")
                if rect:
                    try:
                        coords = rect.split(";")[0]  # 取左下角
                        lng, lat = coords.split(",")
                        r3 = requests.get("https://restapi.amap.com/v3/geocode/regeo",
                                         params={"key": key, "location": f"{lng},{lat}", "extensions": "base"},
                                         timeout=5)
                        if r3.ok and r3.json().get("status") == "1":
                            comp = r3.json().get("regeocode", {}).get("addressComponent", {})
                            if comp.get("district"):
                                parts = [p for p in [comp.get("province", ""), comp.get("city", "") or comp.get("province", ""), comp.get("district", "")] if p]
                    except: pass
                location = ", ".join(parts) if parts else ""
                user.last_located_at = datetime.utcnow(); db.commit()
                return {"lat": float(lat) if lat else None, "lng": float(lng) if lng else None,
                        "location": location, "province": province, "city": city}
    except: pass
    # 回退到 ip-api
    try:
        import requests
        r = requests.get("http://ip-api.com/json/?fields=status,lat,lon,regionName,city&lang=zh-CN", timeout=8)
        if r.ok:
            d = r.json()
            if d.get("status") == "success":
                parts = [p for p in [d.get("regionName"), d.get("city")] if p]
                user.last_located_at = datetime.utcnow(); db.commit()
                return {"lat": float(d["lat"]), "lng": float(d["lon"]),
                        "location": ", ".join(parts) if parts else ""}
    except: pass
    return {"lat": None, "lng": None, "location": ""}

@router.get("/match/history")
def match_history(page: int = 1, limit: int = 10, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    items = db.query(MatchQueue).filter(MatchQueue.user_id == user.id).order_by(MatchQueue.created_at.desc()).offset((page-1)*limit).limit(limit).all()
    return {"items": [{"id": i.id, "status": i.status, "scope": i.scope, "matched_at": i.matched_at.isoformat() if i.matched_at else None} for i in items]}
