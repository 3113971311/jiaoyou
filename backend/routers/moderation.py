from fastapi import APIRouter, Depends, Request, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session, joinedload
from database import get_db
from models import ReviewQueue, MomentImage, Moment, Notification, User
from schemas import BatchReviewRequest, BatchDeleteRequest
from auth import get_admin_user, verify_token
import os, shutil
from config import UPLOAD_DIR

router = APIRouter(tags=["moderation"])

@router.get("/admin/review-queue")
def get_queue(status: str = "pending", image_type: str = "", page: int = 1, limit: int = 20,
              admin: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    q = db.query(ReviewQueue)
    if status: q = q.filter(ReviewQueue.status == status)
    if image_type: q = q.filter(ReviewQueue.image_type == image_type)
    total = q.count()
    items = q.order_by(ReviewQueue.submitted_at.desc()).offset((page-1)*limit).limit(limit).all()

    # 批量获取关联信息
    submitter_ids = list(set(i.submitted_by for i in items if i.submitted_by))
    reviewer_ids = list(set(i.reviewed_by for i in items if i.reviewed_by))
    moment_ids = list(set(i.related_id for i in items if i.image_type == "moment"))
    users_map = {}
    if submitter_ids or reviewer_ids:
        all_user_ids = submitter_ids + reviewer_ids
        users = db.query(User).filter(User.id.in_(all_user_ids)).all()
        users_map = {u.id: u for u in users}
    moments_map = {}
    if moment_ids:
        moments = db.query(Moment).filter(Moment.id.in_(moment_ids)).all()
        moments_map = {m.id: m for m in moments}

    result = []
    for i in items:
        submitter = users_map.get(i.submitted_by)
        reviewer = users_map.get(i.reviewed_by)
        item_data = {
            "id": i.id, "image_url": i.image_url, "thumbnail_url": i.thumbnail_url or i.image_url,
            "image_type": i.image_type, "status": i.status, "submitted_at": i.submitted_at.isoformat(),
            "review_comment": i.review_comment,
            "submitter": {"id": submitter.id, "username": submitter.username, "nickname": submitter.nickname} if submitter else None,
            "reviewer": {"id": reviewer.id, "username": reviewer.username} if reviewer else None,
        }
        if i.image_type == "moment" and i.related_id in moments_map:
            m = moments_map[i.related_id]
            item_data["related_moment"] = {"id": m.id, "content_text": m.content_text[:200], "status": m.status}
        elif i.image_type == "avatar" and submitter:
            item_data["related_user"] = {"id": submitter.id, "username": submitter.username, "nickname": submitter.nickname, "avatar_staging": submitter.avatar_staging}
        result.append(item_data)

    return {"items": result, "total": total}

@router.post("/admin/review-queue/{item_id}/approve")
def approve(item_id: str, admin: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    item = db.query(ReviewQueue).filter(ReviewQueue.id == item_id).first()
    if not item or item.status != "pending": raise HTTPException(404)
    now = __import__("datetime").datetime.utcnow()
    # 复制文件到 public
    src = os.path.join(UPLOAD_DIR, item.image_url.lstrip("/"))
    dst = os.path.join(UPLOAD_DIR, item.image_url.replace("staging", "public").lstrip("/"))
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    if os.path.exists(src): shutil.copy2(src, dst)
    public_url = item.image_url.replace("staging", "public")
    item.status = "approved"; item.reviewed_by = admin.id; item.reviewed_at = now

    # 更新关联
    if item.image_type == "avatar":
        db.query(User).filter(User.id == item.related_id).update({"avatar_url": public_url, "avatar_staging": None})
    elif item.image_type == "moment":
        db.query(MomentImage).filter(MomentImage.moment_id == item.related_id, MomentImage.image_url == item.image_url).update({"public_url": public_url, "review_status": "approved"})
        pending = db.query(MomentImage).filter(MomentImage.moment_id == item.related_id, MomentImage.review_status == "pending").count()
        if pending == 0:
            db.query(Moment).filter(Moment.id == item.related_id).update({"status": "approved", "reviewed_by": admin.id, "reviewed_at": now})

    db.add(Notification(user_id=item.submitted_by, type="review_approved", title="审核通过", content="你的图片已通过审核"))
    db.commit()
    return {"message": "已通过"}

@router.post("/admin/review-queue/{item_id}/reject")
def reject(item_id: str, req: dict = {}, admin: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    item = db.query(ReviewQueue).filter(ReviewQueue.id == item_id).first()
    if not item: raise HTTPException(404)
    now = __import__("datetime").datetime.utcnow()
    comment = req.get("comment", "")
    item.status = "rejected"; item.reviewed_by = admin.id; item.review_comment = comment
    item.reviewed_at = now
    # 删除暂存文件
    fpath = os.path.join(UPLOAD_DIR, item.image_url.lstrip("/"))
    if os.path.exists(fpath): os.remove(fpath)

    # 更新关联记录
    if item.image_type == "avatar":
        db.query(User).filter(User.id == item.related_id).update({"avatar_staging": None})
    elif item.image_type == "moment":
        db.query(MomentImage).filter(MomentImage.moment_id == item.related_id, MomentImage.image_url == item.image_url).update({"review_status": "rejected"})
        # 如果所有图片都被拒绝，拒绝该动态
        pending_or_approved = db.query(MomentImage).filter(MomentImage.moment_id == item.related_id, MomentImage.review_status.in_(["pending", "approved"])).count()
        if pending_or_approved == 0:
            db.query(Moment).filter(Moment.id == item.related_id).update({"status": "rejected", "review_comment": comment, "reviewed_by": admin.id, "reviewed_at": now})

    db.add(Notification(user_id=item.submitted_by, type="review_rejected", title="审核未通过", content=comment or "你的图片审核未通过"))
    db.commit()
    return {"message": "已拒绝"}

@router.post("/admin/review-queue/batch")
def batch_review(req: BatchReviewRequest, admin: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    for item_id in req.ids:
        if req.action == "approve":
            approve(item_id, admin, db)
        else:
            reject(item_id, {}, admin, db)
    return {"message": f"已处理 {len(req.ids)} 条"}

@router.post("/admin/review-queue/batch-delete")
def batch_delete(req: BatchDeleteRequest, admin: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    for item_id in req.ids:
        item = db.query(ReviewQueue).filter(ReviewQueue.id == item_id).first()
        if item:
            fpath = os.path.join(UPLOAD_DIR, item.image_url.lstrip("/"))
            if os.path.exists(fpath): os.remove(fpath)
            db.delete(item)
    db.commit()
    return {"deleted": len(req.ids)}

# 图片预览（token query param 鉴权，因为 el-image 不带 Authorization header）
@router.get("/admin/image-preview")
def image_preview(img_path: str = Query(..., alias="path"), token: str = Query(...), db: Session = Depends(get_db)):
    try:
        payload = verify_token(token)
        user = db.query(User).filter(User.id == payload["sub"]).first()
        if not user or not user.is_admin: raise HTTPException(403)
    except: raise HTTPException(401)
    safe = img_path.replace("\\", "/").replace("..", "")
    full_path = os.path.join(UPLOAD_DIR, safe.lstrip("/"))
    if not os.path.exists(full_path): raise HTTPException(404)
    return FileResponse(full_path)

# 图片访问（任意登录用户即可，用于前端 el-image）
@router.get("/image")
def serve_image(path: str = Query(...), token: str = Query(...), db: Session = Depends(get_db)):
    try:
        payload = verify_token(token)
        user = db.query(User).filter(User.id == payload["sub"]).first()
        if not user: raise HTTPException(403)
    except: raise HTTPException(401)
    safe = path.replace("\\", "/").replace("..", "")
    full_path = os.path.join(UPLOAD_DIR, safe.lstrip("/"))
    if not os.path.exists(full_path): raise HTTPException(404)
    return FileResponse(full_path)
