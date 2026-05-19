from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import SiteConfig, User
from schemas import UpdateConfigRequest
from auth import get_admin_user

router = APIRouter(tags=["site_config"])

PAYMENT_CONFIG_PREFIXES = ("alipay_", "wechat_")
PUBLIC_CONFIG_KEYS = {
    "announcement_enabled",
    "announcement_text",
    "home_banners",
    "home_notice",
    "site_name",
    "site_subtitle",
}

def is_payment_config_key(key: str) -> bool:
    return key.startswith(PAYMENT_CONFIG_PREFIXES)

@router.get("/site-config")
def get_configs(keys: str = "", db: Session = Depends(get_db)):
    q = db.query(SiteConfig).filter(SiteConfig.config_key.in_(PUBLIC_CONFIG_KEYS))
    if keys:
        allowed_keys = [key for key in keys.split(",") if key in PUBLIC_CONFIG_KEYS]
        q = q.filter(SiteConfig.config_key.in_(allowed_keys))
    result = {c.config_key: {"value": c.config_value, "type": c.value_type} for c in q.all()}
    return result

@router.get("/admin/site-configs")
def admin_list_configs(admin: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    q = db.query(SiteConfig)
    for prefix in PAYMENT_CONFIG_PREFIXES:
        q = q.filter(~SiteConfig.config_key.startswith(prefix))
    return q.all()

@router.put("/admin/site-configs/{key}")
def admin_update_config(key: str, req: UpdateConfigRequest, admin: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    if is_payment_config_key(key):
        raise HTTPException(400, "支付配置已移除")
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
