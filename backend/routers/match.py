from datetime import datetime, timedelta

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from auth import get_current_user, get_vip_user
from database import get_db
from models import Conversation, MatchDailyCount, MatchQueue, Message, Notification, SiteConfig, User
from schemas import StartMatchRequest

router = APIRouter(tags=["match"])


def get_amap_key(db: Session) -> str:
    cfg = db.query(SiteConfig).filter(SiteConfig.config_key == "amap_key").first()
    return (cfg.config_value or "").strip() if cfg else ""


def fetch_json(url: str, *, params: dict | None = None, headers: dict | None = None, timeout: float = 5):
    try:
        response = httpx.get(url, params=params, headers=headers, timeout=timeout, follow_redirects=True)
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    return {}


def format_cn_location(component: dict) -> tuple[str, str, str]:
    province = component.get("province", "") or ""
    city = component.get("city", "") or province
    if isinstance(city, list):
        city = province
    district = component.get("district", "") or ""
    parts = [part for part in [province, city, district] if part]
    province_short = province.replace("省", "").replace("市", "").strip() if province else ""
    return ", ".join(parts) if parts else "", province_short, district


def reverse_geocode(lat: float, lng: float) -> tuple[str, str, str]:
    try:
        db = next(get_db())
        try:
            key = get_amap_key(db)
        finally:
            db.close()
        if not key:
            return "", "", ""
        data = fetch_json(
            "https://restapi.amap.com/v3/geocode/regeo",
            params={"key": key, "location": f"{lng},{lat}", "extensions": "base"},
        )
        if data.get("status") == "1":
            comp = data.get("regeocode", {}).get("addressComponent", {})
            return format_cn_location(comp)
    except Exception:
        pass
    return "", "", ""


@router.post("/match/start")
def start_match(req: StartMatchRequest, user: User = Depends(get_vip_user), db: Session = Depends(get_db)):
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    dc = (
        db.query(MatchDailyCount)
        .filter(MatchDailyCount.user_id == user.id, MatchDailyCount.date >= today)
        .first()
    )
    if dc and dc.count >= 5:
        raise HTTPException(400, "今日匹配次数已用完（5次/天）")

    existing = (
        db.query(MatchQueue)
        .filter(
            MatchQueue.user_id == user.id,
            MatchQueue.status == "waiting",
            MatchQueue.expires_at > datetime.utcnow(),
        )
        .first()
    )
    if existing:
        raise HTTPException(400, "你已在匹配队列中")

    location_str, province, district = reverse_geocode(req.latitude, req.longitude)
    if location_str:
        user.location = location_str
        db.commit()

    prefer = req.prefer_gender or ("male" if user.gender == "female" else "female")
    expires = datetime.utcnow() + timedelta(hours=12)
    me = MatchQueue(
        user_id=user.id,
        scope=req.scope,
        city=district or location_str,
        province=province,
        latitude=req.latitude,
        longitude=req.longitude,
        prefer_gender=prefer,
        expires_at=expires,
    )
    db.add(me)
    db.flush()

    candidates = (
        db.query(MatchQueue)
        .filter(
            MatchQueue.user_id != user.id,
            MatchQueue.status == "waiting",
            MatchQueue.expires_at > datetime.utcnow(),
            MatchQueue.prefer_gender == (user.gender or "male"),
        )
        .order_by(MatchQueue.created_at.asc())
        .all()
    )

    for candidate in candidates:
        same_scope = candidate.scope == req.scope
        same_city = req.scope == "city" and candidate.city == (district or location_str)
        same_province = req.scope == "province" and candidate.province == province
        if same_scope and (same_city or same_province):
            user1_id, user2_id = sorted([user.id, candidate.user_id])
            conv = Conversation(user1_id=user1_id, user2_id=user2_id, last_message_at=datetime.utcnow())
            db.add(conv)
            db.flush()

            me.status = "matched"
            me.matched_with = candidate.user_id
            me.matched_at = datetime.utcnow()
            candidate.status = "matched"
            candidate.matched_with = user.id
            candidate.matched_at = datetime.utcnow()

            content = "你们配对成功，开始聊天吧！"
            db.add(Message(conversation_id=conv.id, sender_id=user.id, content=content))
            for uid in [user.id, candidate.user_id]:
                db.add(Notification(user_id=uid, type="match_success", title="配对成功", content=content))

            if not dc:
                dc = MatchDailyCount(user_id=user.id, date=today, count=1)
                db.add(dc)
            else:
                dc.count += 1

            db.commit()
            return {"matched": True, "conversation_id": conv.id, "matched_user": {"id": candidate.user_id}}

    db.commit()
    return {"message": "已进入匹配队列", "queue_id": me.id}


@router.post("/match/cancel")
def cancel_match(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db.query(MatchQueue).filter(MatchQueue.user_id == user.id, MatchQueue.status == "waiting").update({"status": "cancelled"})
    db.commit()
    return {"message": "已取消"}


@router.get("/match/status")
def match_status(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    active = (
        db.query(MatchQueue)
        .filter(MatchQueue.user_id == user.id, MatchQueue.status.in_(["waiting", "matched"]))
        .order_by(MatchQueue.created_at.desc())
        .first()
    )
    if active and active.status == "waiting" and active.expires_at < datetime.utcnow():
        active.status = "expired"
        db.commit()
        active = None
    if not active:
        return {"is_matching": False, "is_matched": False, "matched_user": None}

    matched_user = None
    if active.matched_with:
        mu = db.query(User).filter(User.id == active.matched_with).first()
        if mu:
            matched_user = {
                "id": mu.id,
                "username": mu.username,
                "nickname": mu.nickname,
                "avatar_url": mu.avatar_url,
            }
    return {
        "is_matching": active.status == "waiting",
        "is_matched": active.status == "matched",
        "matched_user": matched_user,
        "expires_at": active.expires_at.isoformat() if active.expires_at else None,
    }


@router.get("/geocode/search")
def geocode_search(q: str = ""):
    if not q:
        return {"lat": None, "lng": None}
    try:
        data = fetch_json(
            "https://nominatim.openstreetmap.org/search",
            params={"q": q, "format": "json", "limit": 1, "accept-language": "zh"},
            headers={"User-Agent": "FriendChat/1.0"},
        )
        if data:
            item = data[0]
            return {"lat": float(item["lat"]), "lng": float(item["lon"])}
    except Exception:
        pass
    return {"lat": None, "lng": None}


@router.get("/geocode/reverse")
def geocode_reverse(lat: float = 0, lng: float = 0, db: Session = Depends(get_db)):
    if not lat or not lng:
        return {"location": ""}
    key = get_amap_key(db)
    if not key:
        return {"location": ""}
    try:
        data = fetch_json(
            "https://restapi.amap.com/v3/geocode/regeo",
            params={"key": key, "location": f"{lng},{lat}", "extensions": "base"},
        )
        if data.get("status") == "1":
            comp = data.get("regeocode", {}).get("addressComponent", {})
            location, _, _ = format_cn_location(comp)
            return {"location": location}
    except Exception:
        pass
    return {"location": ""}


@router.get("/geocode/ip-locate")
def ip_locate(ip: str = ""):
    if not ip:
        return {"lat": None, "lng": None, "location": ""}
    try:
        data = fetch_json(f"http://ip-api.com/json/{ip}?fields=status,lat,lon,city,regionName,country", timeout=5)
        if data.get("status") == "success":
            parts = [part for part in [data.get("regionName"), data.get("city")] if part]
            return {
                "lat": float(data["lat"]),
                "lng": float(data["lon"]),
                "location": ", ".join(parts) if parts else "",
            }
    except Exception:
        pass
    return {"lat": None, "lng": None, "location": ""}


@router.get("/geocode/my-ip")
def my_ip_locate(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not user.is_admin and user.last_located_at:
        elapsed = datetime.utcnow() - user.last_located_at
        if elapsed < timedelta(hours=24):
            return {
                "lat": None,
                "lng": None,
                "location": "",
                "limited": True,
                "msg": f"每天只能更新一次定位，请{24 - int(elapsed.total_seconds() // 3600)}小时后再试",
            }

    key = get_amap_key(db)
    if not key:
        return {"lat": None, "lng": None, "location": "未配置高德Key"}

    try:
        data = fetch_json("https://restapi.amap.com/v3/ip", params={"key": key}, timeout=8)
        if data.get("status") == "1":
            adcode = data.get("adcode", "")
            province = data.get("province", "")
            city = data.get("city", "")
            district = ""
            lat = None
            lng = None

            if adcode:
                district_data = fetch_json(
                    "https://restapi.amap.com/v3/config/district",
                    params={"key": key, "keywords": "" if len(adcode) < 4 else adcode[:4], "subdistrict": 1},
                )
                districts = district_data.get("districts", [])
                if districts and districts[0].get("districts"):
                    district = districts[0]["districts"][0]["name"]

            rect = data.get("rectangle", "")
            if rect and ";" in rect:
                try:
                    left_bottom, right_top = rect.split(";")
                    lng1, lat1 = left_bottom.split(",")
                    lng2, lat2 = right_top.split(",")
                    lng = round((float(lng1) + float(lng2)) / 2, 6)
                    lat = round((float(lat1) + float(lat2)) / 2, 6)

                    regeo_data = fetch_json(
                        "https://restapi.amap.com/v3/geocode/regeo",
                        params={"key": key, "location": f"{lng},{lat}", "extensions": "base"},
                    )
                    if regeo_data.get("status") == "1":
                        comp = regeo_data.get("regeocode", {}).get("addressComponent", {})
                        location, _, precise_district = format_cn_location(comp)
                        if precise_district:
                            district = precise_district
                            parts = [part for part in location.split(", ") if part]
                        else:
                            parts = [part for part in [province, city, district] if part]
                    else:
                        parts = [part for part in [province, city, district] if part]
                except Exception:
                    parts = [part for part in [province, city, district] if part]
            else:
                parts = [part for part in [province, city, district] if part]

            location = ", ".join(parts) if parts else ""
            user.last_located_at = datetime.utcnow()
            db.commit()
            return {"lat": lat, "lng": lng, "location": location, "province": province, "city": city}
    except Exception:
        pass

    try:
        data = fetch_json("http://ip-api.com/json/?fields=status,lat,lon,regionName,city&lang=zh-CN", timeout=8)
        if data.get("status") == "success":
            parts = [part for part in [data.get("regionName"), data.get("city")] if part]
            user.last_located_at = datetime.utcnow()
            db.commit()
            return {
                "lat": float(data["lat"]),
                "lng": float(data["lon"]),
                "location": ", ".join(parts) if parts else "",
            }
    except Exception:
        pass

    return {"lat": None, "lng": None, "location": ""}


@router.get("/match/history")
def match_history(page: int = 1, limit: int = 10, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    items = (
        db.query(MatchQueue)
        .filter(MatchQueue.user_id == user.id)
        .order_by(MatchQueue.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )
    return {
        "items": [
            {
                "id": item.id,
                "status": item.status,
                "scope": item.scope,
                "matched_at": item.matched_at.isoformat() if item.matched_at else None,
            }
            for item in items
        ]
    }
