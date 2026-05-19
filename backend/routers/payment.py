import json
import os
import uuid
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import or_
from sqlalchemy.orm import Session

from auth import get_admin_user, get_current_user
from config import ENABLE_DEV_PAYMENT, UPLOAD_DIR
from database import get_db
from models import AlipayBill, Card, CardBatch, PaymentOrder, SiteConfig, User, VipOrder, VipPlan
from schemas import BatchBillStatusRequest, RedeemCardRequest, SubmitOrderNoRequest, VipPlanRequest
from utils.alipay_monitor import launch_login_window, monitor_status, poll_match_order, sync_bills_once
from utils.card_code import generate_code, hash_candidates, hash_text
from utils.mailer import send_mail
from utils.uploads import IMAGE_EXTENSIONS, read_validated_upload

router = APIRouter(tags=["payment"])


def parse_amount(value):
    try:
        cleaned = str(value or "").replace(",", "").replace(" ", "").replace("¥", "").replace("￥", "")
        return round(float(cleaned), 2)
    except Exception:
        return None


def parse_dt(value):
    if not value:
        return None
    text = str(value).strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).replace(tzinfo=None)
    except Exception:
        return None


def plan_json(plan):
    return {
        "id": plan.id,
        "days": plan.days,
        "price": plan.price,
        "title": plan.title or f"{plan.days} 天 VIP",
        "description": plan.description or "",
        "badge": plan.badge or "",
        "payment_qr_url": plan.payment_qr_url or "",
        "first_discount_rate": float(plan.first_discount_rate or 0),
        "first_discount_qr_url": plan.first_discount_qr_url or "",
        "sort_order": plan.sort_order or 0,
        "is_active": bool(plan.is_active),
    }


def user_plan_json(plan: VipPlan, user_id: str, db: Session):
    item = plan_json(plan)
    pricing = resolve_order_pricing(plan, user_id, db)
    item["price"] = pricing["amount"]
    item["original_price"] = pricing["original_amount"]
    item["discount_rate"] = pricing["discount_rate"]
    item["is_first_discount"] = pricing["is_first_discount"]
    item["payment_qr_url"] = pricing["payment_qr_url"] or item["payment_qr_url"]
    return item


def bill_json(bill):
    amount = bill.amount if bill.amount is not None else parse_amount(bill.amount_text)
    return {
        "id": bill.id,
        "trade_no": bill.trade_no,
        "order_no": bill.order_no,
        "amount": bill.amount,
        "amount_text": bill.amount_text,
        "posted_at": bill.posted_at.isoformat() if bill.posted_at else None,
        "accounting_type": bill.accounting_type,
        "biz_description": bill.biz_description,
        "payment_memo": bill.payment_memo,
        "remark": bill.remark,
        "counterparty": bill.counterparty,
        "operation": bill.operation,
        "source": bill.source,
        "captured_at": bill.captured_at.isoformat() if bill.captured_at else None,
        "issue_status": bill.issue_status or "pending",
        "direction": "expense" if amount is not None and amount < 0 else "income",
        "consumed_by_order_id": bill.consumed_by_order_id,
    }


def get_site_config_value(db: Session, key: str) -> str:
    cfg = db.query(SiteConfig).filter(SiteConfig.config_key == key).first()
    return (cfg.config_value or "").strip() if cfg else ""


def validate_plan(req: VipPlanRequest):
    if req.days <= 0:
        raise HTTPException(400, "套餐天数必须大于 0")
    if req.price < 0:
        raise HTTPException(400, "套餐价格不能小于 0")
    if not str(req.payment_qr_url or "").strip():
        raise HTTPException(400, "请为套餐上传收款码")
    rate = float(req.first_discount_rate or 0)
    if rate < 0 or rate >= 10:
        raise HTTPException(400, "首次充值折扣必须在 0 到 10 之间，0 表示不启用")
    if rate > 0 and not str(req.first_discount_qr_url or "").strip():
        raise HTTPException(400, "启用首次充值折扣时，请上传首次折扣收款码")


def upsert_bills(records, db: Session):
    stored = []
    for record in records or []:
        bill_id = record.get("id")
        if not bill_id:
            continue
        bill = db.query(AlipayBill).filter(AlipayBill.id == bill_id).first()
        if not bill:
            bill = AlipayBill(id=bill_id)
            db.add(bill)
            bill.issue_status = "pending"

        bill.trade_no = record.get("tradeNo") or record.get("alipayTradeNo") or ""
        bill.order_no = record.get("orderNo") or record.get("bizOrderNo") or ""
        bill.amount = parse_amount(record.get("amount") or record.get("amountCny"))
        bill.amount_text = str(record.get("amount") or record.get("amountCny") or "")
        bill.posted_at = parse_dt(record.get("postedAt") or record.get("time"))
        bill.accounting_type = record.get("accountingType") or ""
        bill.biz_description = record.get("bizDescription") or record.get("title") or ""
        bill.payment_memo = record.get("paymentMemo") or record.get("memo") or ""
        bill.remark = record.get("remark") or ""
        bill.counterparty = record.get("counterparty") or ""
        bill.operation = record.get("operation") or ""
        bill.source = record.get("source") or ""
        bill.captured_at = parse_dt(record.get("capturedAt")) or datetime.utcnow()
        bill.raw_json = json.dumps(record.get("raw") or record, ensure_ascii=False)
        if not bill.issue_status:
            bill.issue_status = "pending"
        stored.append(bill)

    db.commit()
    return stored


def find_bill_for_order(db: Session, submitted_order_no: str, amount: float):
    amount = round(float(amount), 2)
    bill = db.query(AlipayBill).filter(
        AlipayBill.amount >= amount - 0.001,
        AlipayBill.amount <= amount + 0.001,
        AlipayBill.issue_status != "void",
        or_(AlipayBill.order_no == submitted_order_no, AlipayBill.trade_no == submitted_order_no),
    ).order_by(AlipayBill.posted_at.desc()).first()
    return bill


def ensure_order_frequency(user_id: str, db: Session):
    now = datetime.utcnow()
    minute_limit = now - timedelta(minutes=1)
    hour_limit = now - timedelta(hours=1)
    recent_order = (
        db.query(PaymentOrder)
        .filter(PaymentOrder.user_id == user_id, PaymentOrder.created_at >= minute_limit)
        .order_by(PaymentOrder.created_at.desc())
        .first()
    )
    if recent_order:
        raise HTTPException(429, "同一账号每分钟只能发起一次充值订单")

    recent_paid = (
        db.query(PaymentOrder)
        .filter(PaymentOrder.user_id == user_id, PaymentOrder.status == "paid", PaymentOrder.paid_at >= hour_limit)
        .order_by(PaymentOrder.paid_at.desc())
        .first()
    )
    if recent_paid:
        raise HTTPException(429, "同一账号每小时只能完成一次充值")


def resolve_order_pricing(plan: VipPlan, user_id: str, db: Session):
    original_amount = round(float(plan.price), 2)
    discount_rate = round(float(plan.first_discount_rate or 0), 2)
    has_paid_same_plan = (
        db.query(PaymentOrder.id)
        .filter(
            PaymentOrder.user_id == user_id,
            PaymentOrder.plan_days == plan.days,
            PaymentOrder.status == "paid",
        )
        .first()
        is not None
    )
    is_first_discount = discount_rate > 0 and discount_rate < 10 and not has_paid_same_plan
    amount = round(original_amount * discount_rate / 10, 2) if is_first_discount else original_amount
    payment_qr_url = plan.first_discount_qr_url if is_first_discount and plan.first_discount_qr_url else plan.payment_qr_url
    return {
        "amount": amount,
        "original_amount": original_amount,
        "discount_rate": discount_rate if is_first_discount else 0,
        "is_first_discount": is_first_discount,
        "payment_qr_url": payment_qr_url or "",
    }


def create_card_for_order(order: PaymentOrder, db: Session):
    code = generate_code()
    expires = datetime.utcnow() + timedelta(days=365)
    batch = CardBatch(
        batch_name=f"online-{order.plan_days}d",
        denomination_days=order.plan_days,
        expire_days=365,
        quantity=1,
        generated_by=order.user_id,
    )
    db.add(batch)
    db.flush()
    db.add(
        Card(
            batch_id=batch.id,
            card_code=code,
            code_hash=hash_text(code),
            denomination_days=order.plan_days,
            expires_at=expires,
        )
    )
    return code, expires


def fulfill_order(order: PaymentOrder, bill: AlipayBill | None, submitted_order_no: str, db: Session):
    if order.status == "paid" and order.card_code:
        return order.card_code

    code, expires = create_card_for_order(order, db)
    order.trade_no = bill.trade_no if bill and bill.trade_no else submitted_order_no
    order.submitted_order_no = submitted_order_no
    order.verified_bill_id = bill.id if bill else None
    order.verification_message = "支付成功，卡密已发送"
    order.last_checked_at = datetime.utcnow()
    order.status = "paid"
    order.card_code = code
    order.paid_at = datetime.utcnow()
    if bill:
        bill.issue_status = "issued"
        bill.consumed_by_order_id = order.id

    db.commit()

    if order.email:
        send_mail(
            order.email,
            "您购买的 VIP 卡密",
            (
                f"<h3>感谢购买</h3>"
                f"<p>卡密：<b>{code}</b></p>"
                f"<p>面值：{order.plan_days} 天 VIP</p>"
                f"<p>有效期至：{expires.strftime('%Y-%m-%d')}</p>"
            ),
        )
    return code


@router.post("/cards/redeem")
def redeem(req: RedeemCardRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    hashes = hash_candidates(req.code)
    card = db.query(Card).filter(Card.code_hash.in_(hashes)).first()
    if not card:
        raise HTTPException(400, "无效的卡密")
    if card.status != "unused":
        raise HTTPException(400, "该卡密已被使用")
    if card.expires_at < datetime.utcnow():
        raise HTTPException(400, "该卡密已过期")

    card.status = "used"
    card.used_by = user.id
    card.used_at = datetime.utcnow()
    now = datetime.utcnow()
    previous_expiry = user.vip_expires_at if user.vip_expires_at and user.vip_expires_at > now else now
    new_expiry = previous_expiry + timedelta(days=card.denomination_days)
    user.vip_expires_at = new_expiry
    db.add(
        VipOrder(
            user_id=user.id,
            card_id=card.id,
            days=card.denomination_days,
            order_type="card_redeem",
            vip_before=previous_expiry,
            vip_after=new_expiry,
        )
    )
    db.commit()
    return {"success": True, "days": card.denomination_days, "vip_expires_at": new_expiry.isoformat()}


@router.get("/vip/status")
def vip_status(user: User = Depends(get_current_user)):
    is_vip = user.vip_expires_at and user.vip_expires_at > datetime.utcnow()
    remaining = max(0, (user.vip_expires_at - datetime.utcnow()).days) if is_vip else 0
    return {
        "is_vip": is_vip,
        "expires_at": user.vip_expires_at.isoformat() if user.vip_expires_at else None,
        "days_remaining": remaining,
    }


@router.get("/vip/history")
def vip_history(page: int = 1, limit: int = 10, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    items = (
        db.query(VipOrder)
        .filter(VipOrder.user_id == user.id)
        .order_by(VipOrder.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )
    return {"items": [{"id": i.id, "days": i.days, "order_type": i.order_type, "created_at": i.created_at.isoformat()} for i in items]}


@router.get("/vip/plans")
def list_vip_plans(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    plans = db.query(VipPlan).filter(VipPlan.is_active == True).order_by(VipPlan.sort_order.asc(), VipPlan.days.asc()).all()
    return {"items": [user_plan_json(p, user.id, db) for p in plans]}


@router.get("/admin/vip-plans")
def admin_list_vip_plans(admin: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    plans = db.query(VipPlan).order_by(VipPlan.sort_order.asc(), VipPlan.days.asc()).all()
    return {"items": [plan_json(p) for p in plans]}


@router.post("/admin/vip-plans")
def admin_create_vip_plan(req: VipPlanRequest, admin: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    validate_plan(req)
    if db.query(VipPlan).filter(VipPlan.days == req.days).first():
        raise HTTPException(400, "该天数套餐已存在")
    plan = VipPlan(**req.model_dump())
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan_json(plan)


@router.put("/admin/vip-plans/{plan_id}")
def admin_update_vip_plan(plan_id: str, req: VipPlanRequest, admin: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    validate_plan(req)
    plan = db.query(VipPlan).filter(VipPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(404, "套餐不存在")
    exists = db.query(VipPlan).filter(VipPlan.days == req.days, VipPlan.id != plan_id).first()
    if exists:
        raise HTTPException(400, "该天数套餐已存在")
    for key, value in req.model_dump().items():
        setattr(plan, key, value)
    plan.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(plan)
    return plan_json(plan)


@router.delete("/admin/vip-plans/{plan_id}")
def admin_delete_vip_plan(plan_id: str, admin: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    plan = db.query(VipPlan).filter(VipPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(404, "套餐不存在")
    db.delete(plan)
    db.commit()
    return {"message": "已删除"}


@router.post("/payment/orders")
def create_order(days: int = 30, email: str = "", method: str = "alipay", user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ensure_order_frequency(user.id, db)
    plan = db.query(VipPlan).filter(VipPlan.days == days, VipPlan.is_active == True).first()
    if not plan:
        raise HTTPException(400, "套餐不存在或已停用")
    pricing = resolve_order_pricing(plan, user.id, db)
    order = PaymentOrder(
        user_id=user.id,
        plan_days=days,
        amount=pricing["amount"],
        original_amount=pricing["original_amount"],
        discount_rate=pricing["discount_rate"],
        is_first_discount=pricing["is_first_discount"],
        email=email,
        payment_method=method,
        payment_qr_url=pricing["payment_qr_url"],
        status="pending",
        verification_message="等待用户提交支付宝订单号",
    )
    if not order.payment_qr_url:
        raise HTTPException(400, "该套餐暂未配置收款码，请联系管理员")
    db.add(order)
    db.commit()
    db.refresh(order)
    return {
        "order_id": order.id,
        "amount": order.amount,
        "original_amount": order.original_amount,
        "discount_rate": order.discount_rate,
        "is_first_discount": bool(order.is_first_discount),
        "days": days,
        "method": method,
        "status": order.status,
        "payment_qr_url": order.payment_qr_url,
    }


@router.post("/payment/orders/{order_id}/submit-order-no")
def submit_order_no(order_id: str, req: SubmitOrderNoRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    order = db.query(PaymentOrder).filter(PaymentOrder.id == order_id, PaymentOrder.user_id == user.id).first()
    if not order:
        raise HTTPException(404, "订单不存在")
    if order.status == "paid":
        return {
            "matched": True,
            "message": "订单已支付完成",
            "card_code": order.card_code,
            "order_id": order.id,
        }

    submitted_order_no = req.order_no.strip()
    if not submitted_order_no:
        raise HTTPException(400, "请输入支付宝订单号")

    order.status = "verifying"
    order.submitted_order_no = submitted_order_no
    order.verification_message = "正在核验支付宝账单"
    order.last_checked_at = datetime.utcnow()
    db.commit()

    try:
        payload = poll_match_order(submitted_order_no, order.amount, timeout_ms=60_000, poll_interval_ms=3_000)
    except RuntimeError as exc:
        order.status = "pending"
        order.verification_message = str(exc)
        order.last_checked_at = datetime.utcnow()
        db.commit()
        raise HTTPException(500, str(exc))

    upsert_bills(payload.get("records") or [], db)

    if payload.get("loginRequired"):
        order.status = "pending"
        order.verification_message = "支付宝账单登录已失效，请联系站长重新登录"
        order.last_checked_at = datetime.utcnow()
        db.commit()
        return {"matched": False, "message": order.verification_message, "login_required": True}

    bill = find_bill_for_order(db, submitted_order_no, order.amount)
    if not bill:
        order.status = "pending"
        order.verification_message = "未找到订单"
        order.last_checked_at = datetime.utcnow()
        db.commit()
        return {"matched": False, "message": "未找到订单"}

    if bill.consumed_by_order_id and bill.consumed_by_order_id != order.id:
        order.status = "pending"
        order.verification_message = "该支付宝订单号已被使用"
        order.last_checked_at = datetime.utcnow()
        db.commit()
        raise HTTPException(400, "该支付宝订单号已被使用")
    if (bill.issue_status or "pending") == "issued" and bill.consumed_by_order_id != order.id:
        order.status = "pending"
        order.verification_message = "该支付宝账单已标记为已发卡"
        order.last_checked_at = datetime.utcnow()
        db.commit()
        raise HTTPException(400, "该支付宝账单已标记为已发卡")

    code = fulfill_order(order, bill, submitted_order_no, db)
    return {
        "matched": True,
        "message": "支付成功，卡密已发送至邮箱",
        "card_code": code,
        "order_id": order.id,
        "bill": bill_json(bill),
    }


@router.post("/payment/alipay/pay")
def alipay_pay(order_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    order = db.query(PaymentOrder).filter(PaymentOrder.id == order_id, PaymentOrder.user_id == user.id).first()
    if not order:
        raise HTTPException(404, "订单不存在")
    raise HTTPException(400, "请完成付款后手动提交支付宝订单号")


@router.post("/payment/alipay/notify")
async def alipay_notify():
    return "success"


@router.post("/payment/dev-pay")
def dev_pay(order_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not ENABLE_DEV_PAYMENT:
        raise HTTPException(404, "开发支付仅在调试环境开放")
    order = db.query(PaymentOrder).filter(PaymentOrder.id == order_id, PaymentOrder.user_id == user.id).first()
    if not order:
        raise HTTPException(404, "订单不存在")
    if order.status == "paid":
        return {"success": True, "card_code": order.card_code, "days": order.plan_days}
    code = fulfill_order(order, None, f"DEV_{uuid.uuid4().hex[:12].upper()}", db)
    return {"success": True, "card_code": code, "days": order.plan_days}


@router.get("/payment/orders/{order_id}")
def get_order(order_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    order = db.query(PaymentOrder).filter(PaymentOrder.id == order_id, PaymentOrder.user_id == user.id).first()
    if not order:
        raise HTTPException(404, "订单不存在")
    return {
        "id": order.id,
        "status": order.status,
        "amount": order.amount,
        "original_amount": order.original_amount,
        "discount_rate": order.discount_rate or 0,
        "is_first_discount": bool(order.is_first_discount),
        "days": order.plan_days,
        "card_code": order.card_code,
        "method": order.payment_method,
        "payment_qr_url": order.payment_qr_url,
        "submitted_order_no": order.submitted_order_no,
        "verification_message": order.verification_message,
        "verified_bill_id": order.verified_bill_id,
        "created_at": order.created_at.isoformat(),
        "paid_at": order.paid_at.isoformat() if order.paid_at else None,
    }


@router.post("/admin/vip-plans/upload-qr")
async def admin_upload_vip_plan_qr(
    file: UploadFile = File(...),
    admin: User = Depends(get_admin_user),
):
    upload = await read_validated_upload(
        file,
        max_bytes=5 * 1024 * 1024,
        allowed_kinds={"image"},
        allowed_extensions=IMAGE_EXTENSIONS,
        fallback_extension=".png",
        label="收款码图片",
    )
    if not file.filename:
        raise HTTPException(400, "请选择图片文件")
    if file.content_type and not file.content_type.startswith("image/"):
        raise HTTPException(400, "只能上传图片文件")
    ext = upload["ext"]
    fname = f"{uuid.uuid4()}{ext}"
    public_dir = os.path.join(UPLOAD_DIR, "public", "payment-qr")
    os.makedirs(public_dir, exist_ok=True)
    fpath = os.path.join(public_dir, fname)
    with open(fpath, "wb") as f:
        f.write(upload["content"])
    return {"url": f"/public/payment-qr/{fname}"}


@router.post("/admin/alipay/login")
def admin_alipay_login(admin: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    account = get_site_config_value(db, "bill_monitor_alipay_account")
    password = get_site_config_value(db, "bill_monitor_alipay_password")
    payload = launch_login_window(account, password)
    return {
        "message": payload.get("message") or "支付宝登录窗口已打开",
        "status": payload,
        "auto_login_enabled": bool(account and password),
    }


@router.get("/admin/alipay/status")
def admin_alipay_status(admin: User = Depends(get_admin_user)):
    try:
        payload = monitor_status()
    except RuntimeError as exc:
        raise HTTPException(500, str(exc))
    return payload


@router.post("/admin/alipay/bills/sync")
def admin_sync_alipay_bills(admin: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    try:
        payload = sync_bills_once()
    except RuntimeError as exc:
        raise HTTPException(500, str(exc))
    stored = upsert_bills(payload.get("records") or [], db)
    return {"message": "账单同步完成", "count": len(stored), "login_required": bool(payload.get("loginRequired"))}


@router.get("/admin/alipay/bills")
def admin_list_alipay_bills(
    page: int = 1,
    limit: int = 20,
    query: str = "",
    direction: str = "income",
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    q = db.query(AlipayBill)
    if direction == "income":
        q = q.filter(AlipayBill.amount >= 0)
    elif direction == "expense":
        q = q.filter(AlipayBill.amount < 0)
    if query:
        like = f"%{query}%"
        q = q.filter(
            or_(
                AlipayBill.trade_no.like(like),
                AlipayBill.order_no.like(like),
                AlipayBill.counterparty.like(like),
                AlipayBill.biz_description.like(like),
            )
        )
    total = q.count()
    items = q.order_by(AlipayBill.posted_at.desc(), AlipayBill.created_at.desc()).offset((page - 1) * limit).limit(limit).all()
    return {"items": [bill_json(i) for i in items], "total": total}


@router.get("/admin/alipay/bills/{bill_id}")
def admin_get_alipay_bill(bill_id: str, admin: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    bill = db.query(AlipayBill).filter(AlipayBill.id == bill_id).first()
    if not bill:
        raise HTTPException(404, "账单不存在")
    data = bill_json(bill)
    try:
        data["raw"] = json.loads(bill.raw_json) if bill.raw_json else {}
    except Exception:
        data["raw"] = {}
    return data


@router.post("/admin/alipay/bills/batch-status")
def admin_batch_update_alipay_bill_status(
    req: BatchBillStatusRequest,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    allowed = {"pending", "issued", "void"}
    target_status = str(req.status or "").strip()
    if target_status not in allowed:
        raise HTTPException(400, "状态必须为 pending、issued 或 void")
    ids = [str(item).strip() for item in req.ids if str(item).strip()]
    if not ids:
        raise HTTPException(400, "请选择账单")

    bills = db.query(AlipayBill).filter(AlipayBill.id.in_(ids)).all()
    updated = 0
    blocked = []
    for bill in bills:
        if bill.consumed_by_order_id and target_status != "issued":
            blocked.append(bill.id)
            continue
        bill.issue_status = target_status
        updated += 1

    db.commit()
    return {"updated": updated, "blocked_ids": blocked, "status": target_status}
