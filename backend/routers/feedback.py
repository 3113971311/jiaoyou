from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import User, SiteConfig
from schemas import FeedbackRequest
from auth import get_current_user
from utils.mailer import send_mail

router = APIRouter(tags=["feedback"])

@router.post("/feedback")
def submit_feedback(req: FeedbackRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    cfg = db.query(SiteConfig).filter(SiteConfig.config_key == "smtp_user").first()
    admin_email = cfg.config_value if cfg else ""
    if admin_email:
        body = f"<h3>用户反馈</h3><p>用户：{user.username} ({user.nickname or '-'})</p><p>标题：{req.title}</p><pre>{req.content}</pre><p>联系方式：{req.contact or '未提供'}</p>"
        send_mail(admin_email, f"【用户反馈】{req.title}", body)
    return {"message": "反馈已提交"}
