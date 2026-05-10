from fastapi import APIRouter, Depends, HTTPException, UploadFile, Form
from sqlalchemy.orm import Session
from database import get_db
from models import Moment, MomentImage, MomentLike, MomentComment, ReviewQueue, Follow, Notification, User
from auth import get_current_user, get_vip_user
import os, uuid
from config import UPLOAD_DIR
from datetime import datetime

router = APIRouter(tags=["moments"])

@router.post("/moments")
async def create_moment(content_text: str = Form(""), images: list[UploadFile] = [],
                        user: User = Depends(get_vip_user), db: Session = Depends(get_db)):
    # 每日3条限制
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    if db.query(Moment).filter(Moment.user_id == user.id, Moment.created_at >= today).count() >= 3:
        raise HTTPException(400, "今日发布次数已用完（3条/天）")

    has_images = bool([i for i in images if i.filename])
    initial_status = "pending_review" if has_images else "approved"
    moment = Moment(user_id=user.id, content_text=content_text, status=initial_status)
    db.add(moment); db.flush()

    for i, img in enumerate(images):
        if not img.filename: continue
        ext = os.path.splitext(img.filename)[1] or ".jpg"
        fname = f"{uuid.uuid4()}{ext}"
        staging_dir = os.path.join(UPLOAD_DIR, "staging", "moment")
        os.makedirs(staging_dir, exist_ok=True)
        fpath = os.path.join(staging_dir, fname)
        content = await img.read()
        with open(fpath, "wb") as f: f.write(content)
        rel_path = f"/staging/moment/{fname}"
        db.add(MomentImage(moment_id=moment.id, image_url=rel_path, thumbnail_url=rel_path, sort_order=i))
        db.add(ReviewQueue(image_url=rel_path, image_type="moment", related_id=moment.id, submitted_by=user.id))

    db.commit()
    return {"id": moment.id, "status": moment.status, "message": "动态已提交" if has_images else "动态发布成功"}

@router.get("/moments")
def get_feed(cursor: str = "", limit: int = 20, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # 互关用户的动态 + 自己的
    mutual_ids = [r[0] for r in db.query(Follow.followed_id).filter(Follow.follower_id == user.id).all()]
    visible_ids = set(mutual_ids + [user.id])
    q = db.query(Moment).filter(Moment.user_id.in_(visible_ids), Moment.status == "approved").order_by(Moment.created_at.desc())
    if cursor: q = q.filter(Moment.id < cursor)
    items = q.limit(limit + 1).all()
    has_more = len(items) > limit
    return {"list": [{"id": m.id, "content_text": m.content_text, "created_at": m.created_at.isoformat(),
            "user": {"id": m.user.id, "username": m.user.username, "nickname": m.user.nickname, "avatar_url": m.user.avatar_url},
            "images": [{"url": img.public_url or img.thumbnail_url, "thumb": img.thumbnail_url} for img in m.images],
            "like_count": len(m.likes), "comment_count": len(m.comments)} for m in (items[:limit] if has_more else items)],
            "next_cursor": items[limit-1].id if has_more else None}

@router.get("/moments/{moment_id}")
def get_moment(moment_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    m = db.query(Moment).filter(Moment.id == moment_id).first()
    if not m: raise HTTPException(404)
    return {"id": m.id, "content_text": m.content_text, "status": m.status, "created_at": m.created_at.isoformat(),
            "user": {"id": m.user.id, "username": m.user.username, "nickname": m.user.nickname, "avatar_url": m.user.avatar_url},
            "images": [{"url": img.public_url or img.thumbnail_url, "thumb": img.thumbnail_url} for img in m.images],
            "like_count": len(m.likes), "comment_count": len(m.comments)}

@router.delete("/moments/{moment_id}")
def delete_moment(moment_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    m = db.query(Moment).filter(Moment.id == moment_id).first()
    if not m or m.user_id != user.id: raise HTTPException(404)
    db.delete(m); db.commit()
    return {"message": "已删除"}

@router.post("/moments/{moment_id}/like")
def toggle_like(moment_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    like = db.query(MomentLike).filter(MomentLike.moment_id == moment_id, MomentLike.user_id == user.id).first()
    if like: db.delete(like); db.commit(); return {"liked": False, "like_count": db.query(MomentLike).filter(MomentLike.moment_id == moment_id).count()}
    db.add(MomentLike(moment_id=moment_id, user_id=user.id)); db.commit()
    m = db.query(Moment).filter(Moment.id == moment_id).first()
    if m and m.user_id != user.id:
        db.add(Notification(user_id=m.user_id, type="moment_liked", title="新的赞", content="有人赞了你的动态"))
        db.commit()
    return {"liked": True, "like_count": db.query(MomentLike).filter(MomentLike.moment_id == moment_id).count()}

@router.post("/moments/{moment_id}/comments")
def add_comment(moment_id: str, req: dict, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    c = MomentComment(moment_id=moment_id, user_id=user.id, content=req.get("content", ""))
    db.add(c); db.commit()
    m = db.query(Moment).filter(Moment.id == moment_id).first()
    if m and m.user_id != user.id:
        db.add(Notification(user_id=m.user_id, type="moment_commented", title="新的评论", content=req.get("content", "")[:100]))
        db.commit()
    return {"id": c.id, "content": c.content, "created_at": c.created_at.isoformat(),
            "user": {"id": user.id, "username": user.username, "nickname": user.nickname}}

@router.get("/moments/{moment_id}/comments")
def get_comments(moment_id: str, cursor: str = "", limit: int = 20, db: Session = Depends(get_db)):
    q = db.query(MomentComment).filter(MomentComment.moment_id == moment_id).order_by(MomentComment.created_at.asc())
    items = q.limit(limit+1).all()
    return {"list": [{"id": c.id, "content": c.content, "created_at": c.created_at.isoformat(),
            "user": {"id": c.user_id, "username": "", "nickname": ""}} for c in items[:limit]]}
