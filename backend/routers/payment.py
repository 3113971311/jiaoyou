from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Card, VipOrder, User, CardBatch, PaymentOrder, SiteConfig
from schemas import RedeemCardRequest
from auth import get_current_user
from utils.card_code import hash_text, generate_code
from utils.mailer import send_mail
from datetime import datetime, timedelta
import json, base64, hashlib, time, uuid

router = APIRouter(tags=["payment"])

PLANS = {7: 9.9, 30: 29.9, 90: 69.9, 180: 119.9, 360: 199.9}

def get_payment_config(db):
    cfgs = {}
    for c in db.query(SiteConfig).filter(SiteConfig.config_key.like('alipay_%') | SiteConfig.config_key.like('wechat_%')).all():
        cfgs[c.config_key] = c.config_value
    return cfgs

# ─── Card Redeem ───
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
    remaining = max(0, (user.vip_expires_at - datetime.utcnow()).days) if is_vip else 0
    return {"is_vip": is_vip, "expires_at": user.vip_expires_at.isoformat() if user.vip_expires_at else None, "days_remaining": remaining}

@router.get("/vip/history")
def vip_history(page: int = 1, limit: int = 10, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    items = db.query(VipOrder).filter(VipOrder.user_id == user.id).order_by(VipOrder.created_at.desc()).offset((page-1)*limit).limit(limit).all()
    return {"items": [{"id": i.id, "days": i.days, "order_type": i.order_type, "created_at": i.created_at.isoformat()} for i in items]}

# ─── Payment Order ───
@router.post("/payment/orders")
def create_order(days: int = 30, email: str = "", method: str = "alipay",
                  user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if days not in PLANS: raise HTTPException(400, "无效套餐")
    amount = PLANS[days]
    order = PaymentOrder(user_id=user.id, plan_days=days, amount=amount, email=email, payment_method=method)
    db.add(order); db.commit(); db.refresh(order)
    return {"order_id": order.id, "amount": amount, "days": days, "method": method}

# ─── Alipay PC Website Payment ───
@router.post("/payment/alipay/pay")
def alipay_pay(order_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    order = db.query(PaymentOrder).filter(PaymentOrder.id == order_id, PaymentOrder.user_id == user.id).first()
    if not order: raise HTTPException(404, "订单不存在")
    if order.status != "pending": raise HTTPException(400, "订单已处理")

    cfgs = get_payment_config(db)
    app_id = cfgs.get("alipay_app_id", "")
    private_key = cfgs.get("alipay_private_key", "")
    alipay_public_key = cfgs.get("alipay_public_key", "")

    if not all([app_id, private_key]):
        raise HTTPException(400, "支付宝未配置，请联系管理员")

    try:
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import padding
        from cryptography.hazmat.backends import default_backend

        # Build biz_content
        biz = {
            "out_trade_no": order.id,
            "product_code": "FAST_INSTANT_TRADE_PAY",
            "total_amount": order.amount,
            "subject": f"VIP会员 {order.plan_days}天",
            "body": f"拾光VIP {order.plan_days}天会员卡密",
        }

        params = {
            "app_id": app_id,
            "method": "alipay.trade.page.pay",
            "format": "JSON",
            "charset": "utf-8",
            "sign_type": "RSA2",
            "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            "version": "1.0",
            "notify_url": "",
            "biz_content": json.dumps(biz, ensure_ascii=False),
        }

        # Build sign string
        sorted_keys = sorted(params.keys())
        sign_str = "&".join(f"{k}={params[k]}" for k in sorted_keys if params[k])

        # Sign with RSA-SHA256
        key = serialization.load_pem_private_key(private_key.encode(), password=None, backend=default_backend())
        signature = key.sign(sign_str.encode(), padding.PKCS1v15(), hashes.SHA256())
        sign_base64 = base64.b64encode(signature).decode()
        params["sign"] = sign_base64

        from urllib.parse import urlencode
        gateway = "https://openapi.alipay.com/gateway.do"
        pay_url = f"{gateway}?{urlencode(params)}"

        return {"pay_url": pay_url}
    except Exception as e:
        raise HTTPException(500, f"生成支付链接失败: {str(e)}")

# ─── Alipay Callback ───
@router.post("/payment/alipay/notify")
async def alipay_notify(request=None, db: Session = Depends(get_db)):
    # In production: verify signature, check trade status
    # For now: process the callback params
    try:
        from fastapi import Request
        body = await request.body() if request else b""
        from urllib.parse import parse_qs
        params = parse_qs(body.decode()) if body else {}
        out_trade_no = params.get("out_trade_no", [None])[0]
        trade_no = params.get("trade_no", [None])[0]
        trade_status = params.get("trade_status", [None])[0]

        if out_trade_no and trade_status == "TRADE_SUCCESS":
            order = db.query(PaymentOrder).filter(PaymentOrder.id == out_trade_no).first()
            if order and order.status == "pending":
                complete_order(order, trade_no, db)
        return "success"
    except Exception:
        return "fail"

# ─── Dev/Test Payment (for when credentials not configured) ───
@router.post("/payment/dev-pay")
def dev_pay(order_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    order = db.query(PaymentOrder).filter(PaymentOrder.id == order_id, PaymentOrder.user_id == user.id).first()
    if not order: raise HTTPException(404, "订单不存在")
    if order.status != "pending": raise HTTPException(400, "订单已处理")

    trade_no = "DEV_" + uuid.uuid4().hex[:12].upper()
    code = complete_order(order, trade_no, db)
    return {"success": True, "card_code": code, "days": order.plan_days}

# ─── Order Status ───
@router.get("/payment/orders/{order_id}")
def get_order(order_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    order = db.query(PaymentOrder).filter(PaymentOrder.id == order_id, PaymentOrder.user_id == user.id).first()
    if not order: raise HTTPException(404)
    return {"id": order.id, "status": order.status, "amount": order.amount, "days": order.plan_days,
            "card_code": order.card_code, "method": order.payment_method, "created_at": order.created_at.isoformat()}

# ─── Complete order ───
def complete_order(order, trade_no, db):
    order.trade_no = trade_no
    order.status = "paid"
    order.paid_at = datetime.utcnow()

    code = generate_code()
    h = hash_text(code)
    expires = datetime.utcnow() + timedelta(days=365)
    batch = CardBatch(batch_name=f"线上购买-{order.plan_days}天", denomination_days=order.plan_days,
                      expire_days=365, quantity=1, generated_by=order.user_id)
    db.add(batch); db.flush()
    db.add(Card(batch_id=batch.id, card_code=code, code_hash=h, denomination_days=order.plan_days, expires_at=expires))
    order.card_code = code
    db.commit()

    if order.email:
        send_mail(order.email, "您购买的VIP卡密",
                  f"<h3>感谢购买！</h3><p>卡密：<b>{code}</b></p><p>面值：{order.plan_days}天VIP</p><p>有效期至：{expires.strftime('%Y-%m-%d')}</p>")
    return code
