from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Card, VipOrder, User, CardBatch
from schemas import RedeemCardRequest, BuyCardRequest
from auth import get_current_user
from utils.card_code import hash_text
from utils.mailer import send_mail
from datetime import datetime, timedelta

router = APIRouter(tags=["payment"])

@router.post("/cards/redeem")
def redeem(req: RedeemCardRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    h = hash_text(req.code)
    card = db.query(Card).filter(Card.code_hash == h).first()
    if not card: raise HTTPException(400, "无效的卡密")
    if card.status != "unused": raise HTTPException(400, "该卡密已被使用")
    if card.expires_at < datetime.utcnow(): raise HTTPException(400, "该卡密已过期")

    card.status = "used"; card.used_by = user.id; card.used_at = datetime.utcnow()
    now = datetime.utcnow()
    base = user.vip_expires_at if user.vip_expires_at and user.vip_expires_at > now else now
    new_expiry = base + timedelta(days=card.denomination_days)
    user.vip_expires_at = new_expiry
    db.add(VipOrder(user_id=user.id, card_id=card.id, days=card.denomination_days, order_type="card_redeem",
                    vip_before=user.vip_expires_at, vip_after=new_expiry))
    db.commit()
    return {"success": True, "days": card.denomination_days, "vip_expires_at": new_expiry.isoformat()}

@router.get("/vip/status")
def vip_status(user: User = Depends(get_current_user)):
    is_vip = user.vip_expires_at and user.vip_expires_at > datetime.utcnow()
    remaining = (user.vip_expires_at - datetime.utcnow()).days if is_vip else 0
    return {"is_vip": is_vip, "expires_at": user.vip_expires_at.isoformat() if user.vip_expires_at else None, "days_remaining": remaining}

@router.get("/vip/history")
def vip_history(page: int = 1, limit: int = 10, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    items = db.query(VipOrder).filter(VipOrder.user_id == user.id).order_by(VipOrder.created_at.desc()).offset((page-1)*limit).limit(limit).all()
    return {"items": [{"id": i.id, "days": i.days, "order_type": i.order_type, "created_at": i.created_at.isoformat()} for i in items]}

@router.post("/cards/buy")
def buy_card(req: BuyCardRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    PLANS = {7: 9.9, 30: 29.9, 90: 69.9, 180: 119.9, 360: 199.9}
    if req.days not in PLANS: raise HTTPException(400, "无效套餐")
    from utils.card_code import generate_code
    code = generate_code()
    h = hash_text(code)
    expires = datetime.utcnow() + timedelta(days=365)
    batch = CardBatch(batch_name=f"购买-{req.days}天", denomination_days=req.days, expire_days=365, quantity=1, generated_by=user.id)
    db.add(batch); db.flush()
    db.add(Card(batch_id=batch.id, card_code=code, code_hash=h, denomination_days=req.days, expires_at=expires))
    db.commit()
    send_mail(req.email, "您购买的VIP卡密", f"<h3>卡密：{code}</h3><p>面值：{req.days}天VIP</p><p>有效期至：{expires.strftime('%Y-%m-%d')}</p>")
    return {"message": "购买成功，卡密已发送至邮箱"}
