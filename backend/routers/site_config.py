from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import SiteConfig, User
from schemas import UpdateConfigRequest
from auth import get_admin_user

router = APIRouter(tags=["site_config"])

@router.get("/site-config")
def get_configs(keys: str = "", db: Session = Depends(get_db)):
    q = db.query(SiteConfig)
    if keys: q = q.filter(SiteConfig.config_key.in_(keys.split(",")))
    result = {c.config_key: {"value": c.config_value, "type": c.value_type} for c in q.all()}
    return result

@router.get("/admin/site-configs")
def admin_list_configs(admin: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    return db.query(SiteConfig).all()

@router.put("/admin/site-configs/{key}")
def admin_update_config(key: str, req: UpdateConfigRequest, admin: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    cfg = db.query(SiteConfig).filter(SiteConfig.config_key == key).first()
    if cfg:
        cfg.config_value = req.value
        if req.type: cfg.value_type = req.type
        if req.description: cfg.description = req.description
        cfg.updated_by = admin.id
    else:
        db.add(SiteConfig(config_key=key, config_value=req.value, value_type=req.type or "text", description=req.description, updated_by=admin.id))
    db.commit()
    return {"message": "已保存"}
