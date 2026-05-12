from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import CardBatch, Card, User
from schemas import GenerateCardRequest
from auth import get_admin_user
from utils.card_code import generate_code, hash_text
from datetime import datetime, timedelta

router = APIRouter(tags=["cards"])

@router.post("/admin/cards/generate")
def generate_batch(req: GenerateCardRequest, admin: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    batch = CardBatch(batch_name=req.batch_name, denomination_days=req.denomination_days, expire_days=req.expire_days, quantity=req.quantity, generated_by=admin.id, note=req.note)
    db.add(batch); db.flush()
    codes = []
    expires = datetime.utcnow() + timedelta(days=req.expire_days)
    for _ in range(req.quantity):
        code = generate_code()
        codes.append(code)
        db.add(Card(batch_id=batch.id, card_code=code, code_hash=hash_text(code), denomination_days=req.denomination_days, expires_at=expires))
    db.commit()
    return {"batch_id": batch.id, "batch_name": batch.batch_name, "quantity": req.quantity, "denomination_days": req.denomination_days, "expire_days": req.expire_days, "codes": codes}

@router.get("/admin/cards/batches")
def list_batches(page: int = 1, limit: int = 20, admin: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    items = db.query(CardBatch).order_by(CardBatch.created_at.desc()).offset((page-1)*limit).limit(limit).all()
    total = db.query(CardBatch).count()
    def stats(b):
        cards = db.query(Card).filter(Card.batch_id == b.id).all()
        return {"used": sum(1 for c in cards if c.status == "used"), "unused": sum(1 for c in cards if c.status == "unused"), "expired": sum(1 for c in cards if c.status == "expired")}
    return {"items": [{"id": b.id, "batch_name": b.batch_name, "denomination_days": b.denomination_days, "expire_days": b.expire_days, "quantity": b.quantity, **stats(b), "created_at": b.created_at.isoformat()} for b in items], "total": total}

@router.get("/admin/cards/batches/{batch_id}")
def batch_detail(batch_id: str, page: int = 1, limit: int = 30, status: str = "", admin: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    batch = db.query(CardBatch).filter(CardBatch.id == batch_id).first()
    if not batch: raise HTTPException(404)
    q = db.query(Card).filter(Card.batch_id == batch_id)
    if status: q = q.filter(Card.status == status)
    total = q.count()
    items = q.order_by(Card.created_at.asc()).offset((page-1)*limit).limit(limit).all()
    return {"batch": {"id": batch.id, "batch_name": batch.batch_name}, "items": [{"id": c.id, "card_code": c.card_code, "denomination_days": c.denomination_days, "status": c.status, "expires_at": c.expires_at.isoformat(), "created_at": c.created_at.isoformat()} for c in items], "total": total}

@router.delete("/admin/cards/{card_id}")
def delete_card(card_id: str, admin: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    db.query(Card).filter(Card.id == card_id).delete()
    db.commit()
    return {"message": "已删除"}

@router.delete("/admin/cards/batches/{batch_id}")
def delete_batch(batch_id: str, admin: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    batch = db.query(CardBatch).filter(CardBatch.id == batch_id).first()
    if not batch: raise HTTPException(404)
    db.query(Card).filter(Card.batch_id == batch_id).delete()
    db.delete(batch)
    db.commit()
    return {"message": "批次已删除"}

@router.get("/admin/cards/batches/{batch_id}/export")
def export_batch(batch_id: str, admin: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    batch = db.query(CardBatch).filter(CardBatch.id == batch_id).first()
    cards = db.query(Card).filter(Card.batch_id == batch_id).order_by(Card.created_at.asc()).all()
    csv = "卡密,面值(天),状态,过期时间\n" + "\n".join(f"{c.card_code},{c.denomination_days},{c.status},{c.expires_at.isoformat()}" for c in cards)
    from fastapi.responses import PlainTextResponse
    return PlainTextResponse(csv, media_type="text/csv", headers={"Content-Disposition": f"attachment; filename={batch.batch_name}.csv"})
