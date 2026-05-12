from fastapi import APIRouter, Depends, HTTPException, UploadFile, Form, Query
from sqlalchemy.orm import Session, joinedload
from database import get_db
from models import Moment, MomentImage, MomentLike, MomentComment, MomentFavorite, ReviewQueue, Follow, Notification, User
from auth import get_current_user, get_vip_user, get_admin_user
import os, uuid
from config import UPLOAD_DIR
from datetime import datetime

router = APIRouter(tags=["moments"])

def _moment_json(m, current_user_id=None):
    """统一的动态序列化，包含 liked/favorited 状态"""
    images = []
    for img in m.images:
        thumb = img.thumbnail_url or img.image_url or ""
        full = img.public_url or thumb
        images.append({"url": full, "thumb": thumb})
    result = {
        "id": m.id, "content_text": m.content_text, "status": m.status,
        "created_at": m.created_at.isoformat(),
        "user": {"id": m.user.id, "username": m.user.username, "nickname": m.user.nickname, "avatar_url": m.user.avatar_url} if m.user else None,
        "images": images,
        "like_count": len(m.likes),
        "comment_count": len(m.comments),
        "favorite_count": len(getattr(m, 'favorites', [])),
    }
    if current_user_id:
        result["liked"] = any(l.user_id == current_user_id for l in m.likes)
        result["favorited"] = any(f.user_id == current_user_id for f in getattr(m, 'favorites', []))
    return result

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
    # 互关用户的已审核动态 + 自己的全部动态（含待审/拒绝）
    mutual_ids = [r[0] for r in db.query(Follow.followed_id).filter(Follow.follower_id == user.id).all()]
    visible_ids = set(mutual_ids)

    # 别人的只显示已审核；自己的全部显示
    from sqlalchemy import or_, and_
    q = db.query(Moment).options(joinedload(Moment.user), joinedload(Moment.images), joinedload(Moment.likes), joinedload(Moment.favorites)).filter(
        or_(
            and_(Moment.user_id.in_(visible_ids), Moment.status == "approved"),
            Moment.user_id == user.id
        )
    ).order_by(Moment.created_at.desc())
    if cursor: q = q.filter(Moment.id < cursor)
    items = q.limit(limit + 1).all()
    has_more = len(items) > limit
    return {"list": [_moment_json(m, user.id) for m in (items[:limit] if has_more else items)],
            "next_cursor": items[limit-1].id if has_more else None}

@router.get("/moments/{moment_id}")
def get_moment(moment_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    m = db.query(Moment).options(joinedload(Moment.user), joinedload(Moment.images), joinedload(Moment.likes), joinedload(Moment.favorites), joinedload(Moment.comments)).filter(Moment.id == moment_id).first()
    if not m: raise HTTPException(404)
    # 别人不能看非 approved 的动态
    if m.user_id != user.id and m.status != "approved":
        raise HTTPException(404, "动态不可见")
    result = _moment_json(m, user.id)
    result["review_comment"] = m.review_comment
    result["comments"] = [{"id": c.id, "content": c.content, "created_at": c.created_at.isoformat(),
            "user": {"id": c.user_id, "username": "", "nickname": ""}} for c in m.comments]
    return result

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

@router.post("/moments/{moment_id}/favorite")
def toggle_favorite(moment_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    fav = db.query(MomentFavorite).filter(MomentFavorite.moment_id == moment_id, MomentFavorite.user_id == user.id).first()
    if fav: db.delete(fav); db.commit(); return {"favorited": False, "favorite_count": db.query(MomentFavorite).filter(MomentFavorite.moment_id == moment_id).count()}
    db.add(MomentFavorite(moment_id=moment_id, user_id=user.id)); db.commit()
    return {"favorited": True, "favorite_count": db.query(MomentFavorite).filter(MomentFavorite.moment_id == moment_id).count()}

@router.get("/users/me/likes")
def my_likes(page: int = 1, limit: int = 20, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    q = db.query(MomentLike).filter(MomentLike.user_id == user.id).order_by(MomentLike.created_at.desc())
    total = q.count()
    items = q.offset((page-1)*limit).limit(limit).all()
    moment_ids = [l.moment_id for l in items]
    moments = db.query(Moment).options(joinedload(Moment.user), joinedload(Moment.images), joinedload(Moment.likes), joinedload(Moment.favorites)).filter(Moment.id.in_(moment_ids)).all() if moment_ids else []
    m_map = {m.id: m for m in moments}
    return {"items": [_moment_json(m_map[l.moment_id], user.id) for l in items if l.moment_id in m_map], "total": total}

@router.get("/users/me/favorites")
def my_favorites(page: int = 1, limit: int = 20, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    q = db.query(MomentFavorite).filter(MomentFavorite.user_id == user.id).order_by(MomentFavorite.created_at.desc())
    total = q.count()
    items = q.offset((page-1)*limit).limit(limit).all()
    moment_ids = [f.moment_id for f in items]
    moments = db.query(Moment).options(joinedload(Moment.user), joinedload(Moment.images), joinedload(Moment.likes), joinedload(Moment.favorites)).filter(Moment.id.in_(moment_ids)).all() if moment_ids else []
    m_map = {m.id: m for m in moments}
    return {"items": [_moment_json(m_map[f.moment_id], user.id) for f in items if f.moment_id in m_map], "total": total}

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
    user_ids = list(set(c.user_id for c in items if c.user_id))
    users = {u.id: u for u in db.query(User).filter(User.id.in_(user_ids)).all()} if user_ids else {}
    return {"list": [{"id": c.id, "content": c.content, "created_at": c.created_at.isoformat(),
            "user": {"id": c.user_id, "username": users[c.user_id].username if c.user_id in users else "", "nickname": users[c.user_id].nickname if c.user_id in users else ""}} for c in items[:limit]]}

@router.delete("/moments/{moment_id}/comments/{comment_id}")
def delete_comment(moment_id: str, comment_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    c = db.query(MomentComment).filter(MomentComment.id == comment_id, MomentComment.moment_id == moment_id).first()
    if not c: raise HTTPException(404)
    if c.user_id != user.id and not user.is_admin:
        raise HTTPException(403, "只能删除自己的评论")
    db.delete(c); db.commit()
    return {"message": "已删除"}

# ==================== Admin 动态管理 ====================

@router.get("/admin/moments")
def admin_list_moments(status: str = "", search: str = "", page: int = 1, limit: int = 20,
                       admin: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    q = db.query(Moment).options(joinedload(Moment.user), joinedload(Moment.images))
    if status: q = q.filter(Moment.status == status)
    if search:
        q = q.filter(Moment.content_text.contains(search))
    total = q.count()
    items = q.order_by(Moment.created_at.desc()).offset((page-1)*limit).limit(limit).all()
    return {"items": [{
        "id": m.id, "content_text": m.content_text, "status": m.status,
        "review_comment": m.review_comment, "created_at": m.created_at.isoformat(),
        "user": {"id": m.user.id, "username": m.user.username, "nickname": m.user.nickname, "avatar_url": m.user.avatar_url} if m.user else None,
        "images": [{"id": img.id, "image_url": img.image_url, "public_url": img.public_url, "thumbnail_url": img.thumbnail_url or img.image_url, "review_status": img.review_status} for img in m.images],
        "like_count": len(m.likes), "comment_count": len(m.comments),
    } for m in items], "total": total}

@router.get("/admin/moments/{moment_id}")
def admin_get_moment(moment_id: str, admin: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    m = db.query(Moment).options(joinedload(Moment.user), joinedload(Moment.images), joinedload(Moment.likes), joinedload(Moment.comments)).filter(Moment.id == moment_id).first()
    if not m: raise HTTPException(404)
    return {
        "id": m.id, "content_text": m.content_text, "status": m.status,
        "review_comment": m.review_comment, "reviewed_by": m.reviewed_by, "reviewed_at": m.reviewed_at.isoformat() if m.reviewed_at else None,
        "created_at": m.created_at.isoformat(),
        "user": {"id": m.user.id, "username": m.user.username, "nickname": m.user.nickname, "avatar_url": m.user.avatar_url} if m.user else None,
        "images": [{"id": img.id, "image_url": img.image_url, "public_url": img.public_url, "thumbnail_url": img.thumbnail_url or img.image_url, "review_status": img.review_status} for img in m.images],
        "like_count": len(m.likes), "comment_count": len(m.comments),
        "comments": [{"id": c.id, "content": c.content, "created_at": c.created_at.isoformat(), "user_id": c.user_id} for c in m.comments],
    }

@router.put("/admin/moments/{moment_id}")
def admin_update_moment(moment_id: str, req: dict, admin: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    m = db.query(Moment).filter(Moment.id == moment_id).first()
    if not m: raise HTTPException(404)
    if "content_text" in req:
        m.content_text = req["content_text"]
    if "status" in req:
        m.status = req["status"]
        if req["status"] in ("approved", "rejected"):
            m.reviewed_by = admin.id
            m.reviewed_at = datetime.utcnow()
    if "review_comment" in req:
        m.review_comment = req["review_comment"]
    db.commit()
    if req.get("status") == "approved":
        db.add(Notification(user_id=m.user_id, type="review_approved", title="动态审核通过", content="你的动态已通过审核"))
        db.commit()
    elif req.get("status") == "rejected":
        db.add(Notification(user_id=m.user_id, type="review_rejected", title="动态审核未通过", content=req.get("review_comment", "你的动态未通过审核")))
        db.commit()
    return {"message": "已更新"}

@router.delete("/admin/moments/{moment_id}")
def admin_delete_moment(moment_id: str, admin: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    m = db.query(Moment).filter(Moment.id == moment_id).first()
    if not m: raise HTTPException(404)
    for img in m.images:
        if img.image_url:
            fpath = os.path.join(UPLOAD_DIR, img.image_url.lstrip("/"))
            if os.path.exists(fpath): os.remove(fpath)
        db.query(ReviewQueue).filter(ReviewQueue.image_url == img.image_url).delete()
    for img in m.images:
        if img.public_url:
            fpath = os.path.join(UPLOAD_DIR, img.public_url.lstrip("/"))
            if os.path.exists(fpath): os.remove(fpath)
    db.delete(m)
    db.commit()
    return {"message": "已删除"}

@router.post("/admin/moments/{moment_id}/review")
def admin_review_moment(moment_id: str, req: dict, admin: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    """审核动态内容（通过或拒绝）"""
    m = db.query(Moment).filter(Moment.id == moment_id).first()
    if not m: raise HTTPException(404)
    action = req.get("action", "")
    if action not in ("approve", "reject"):
        raise HTTPException(400, "action 必须为 approve 或 reject")
    now = datetime.utcnow()
    if action == "approve":
        m.status = "approved"
        m.review_comment = None
        db.add(Notification(user_id=m.user_id, type="moment_approved", title="动态审核通过", content="你的动态已通过审核"))
    else:
        m.status = "rejected"
        m.review_comment = req.get("comment", "")
        db.add(Notification(user_id=m.user_id, type="moment_rejected", title="动态审核未通过", content=req.get("comment", "你的动态未通过审核")))
    m.reviewed_by = admin.id
    m.reviewed_at = now
    db.commit()
    return {"message": "已审核"}
