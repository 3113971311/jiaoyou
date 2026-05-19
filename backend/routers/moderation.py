import os
import shutil
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import FileResponse
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from auth import get_admin_user, security
from database import get_db
from models import Moment, MomentImage, Notification, ReviewQueue, User
from schemas import BatchDeleteRequest, BatchReviewRequest
from utils.file_access import get_request_user, resolve_upload_path

router = APIRouter(tags=["moderation"])


@router.get("/admin/review-queue")
def get_queue(
    status: str = "pending",
    image_type: str = "",
    page: int = 1,
    limit: int = 20,
    admin: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    q = db.query(ReviewQueue)
    if status:
        q = q.filter(ReviewQueue.status == status)
    if image_type:
        q = q.filter(ReviewQueue.image_type == image_type)
    total = q.count()
    items = q.order_by(ReviewQueue.submitted_at.desc()).offset((page - 1) * limit).limit(limit).all()

    submitter_ids = list(set(i.submitted_by for i in items if i.submitted_by))
    reviewer_ids = list(set(i.reviewed_by for i in items if i.reviewed_by))
    moment_ids = list(set(i.related_id for i in items if i.image_type == "moment"))

    users_map = {}
    if submitter_ids or reviewer_ids:
        users = db.query(User).filter(User.id.in_(submitter_ids + reviewer_ids)).all()
        users_map = {u.id: u for u in users}

    moments_map = {}
    if moment_ids:
        moments = db.query(Moment).filter(Moment.id.in_(moment_ids)).all()
        moments_map = {m.id: m for m in moments}

    result = []
    for item in items:
        submitter = users_map.get(item.submitted_by)
        reviewer = users_map.get(item.reviewed_by)
        payload = {
            "id": item.id,
            "image_url": item.image_url,
            "thumbnail_url": item.thumbnail_url or item.image_url,
            "image_type": item.image_type,
            "status": item.status,
            "submitted_at": item.submitted_at.isoformat(),
            "review_comment": item.review_comment,
            "submitter": {"id": submitter.id, "username": submitter.username, "nickname": submitter.nickname} if submitter else None,
            "reviewer": {"id": reviewer.id, "username": reviewer.username} if reviewer else None,
        }
        if item.image_type == "moment" and item.related_id in moments_map:
            moment = moments_map[item.related_id]
            payload["related_moment"] = {"id": moment.id, "content_text": moment.content_text[:200], "status": moment.status}
        elif item.image_type == "avatar" and submitter:
            payload["related_user"] = {
                "id": submitter.id,
                "username": submitter.username,
                "nickname": submitter.nickname,
                "avatar_staging": submitter.avatar_staging,
            }
        result.append(payload)

    return {"items": result, "total": total}


@router.post("/admin/review-queue/{item_id}/approve")
def approve(item_id: str, admin: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    item = db.query(ReviewQueue).filter(ReviewQueue.id == item_id).first()
    if not item or item.status != "pending":
        raise HTTPException(404)

    now = datetime.utcnow()
    src = resolve_upload_path(item.image_url, allowed_prefixes=("staging",))
    dst = resolve_upload_path(item.image_url.replace("staging", "public", 1), allowed_prefixes=("public",))
    os.makedirs(dst.parent, exist_ok=True)
    if src.exists():
        shutil.copy2(src, dst)

    public_url = item.image_url.replace("staging", "public", 1)
    item.status = "approved"
    item.reviewed_by = admin.id
    item.reviewed_at = now

    if item.image_type == "avatar":
        db.query(User).filter(User.id == item.related_id).update({"avatar_url": public_url, "avatar_staging": None})
    elif item.image_type == "moment":
        db.query(MomentImage).filter(MomentImage.moment_id == item.related_id, MomentImage.image_url == item.image_url).update(
            {"public_url": public_url, "review_status": "approved"}
        )
        pending = db.query(MomentImage).filter(MomentImage.moment_id == item.related_id, MomentImage.review_status == "pending").count()
        if pending == 0:
            db.query(Moment).filter(Moment.id == item.related_id).update({"status": "approved", "reviewed_by": admin.id, "reviewed_at": now})

    db.add(Notification(user_id=item.submitted_by, type="review_approved", title="审核通过", content="你的图片已通过审核"))
    db.commit()
    return {"message": "已通过"}


@router.post("/admin/review-queue/{item_id}/reject")
def reject(item_id: str, req: dict = {}, admin: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    item = db.query(ReviewQueue).filter(ReviewQueue.id == item_id).first()
    if not item:
        raise HTTPException(404)

    now = datetime.utcnow()
    comment = req.get("comment", "")
    item.status = "rejected"
    item.reviewed_by = admin.id
    item.review_comment = comment
    item.reviewed_at = now

    fpath = resolve_upload_path(item.image_url, allowed_prefixes=("staging", "public"))
    if fpath.exists():
        os.remove(fpath)

    if item.image_type == "avatar":
        db.query(User).filter(User.id == item.related_id).update({"avatar_staging": None})
    elif item.image_type == "moment":
        db.query(MomentImage).filter(MomentImage.moment_id == item.related_id, MomentImage.image_url == item.image_url).update({"review_status": "rejected"})
        pending_or_approved = (
            db.query(MomentImage)
            .filter(MomentImage.moment_id == item.related_id, MomentImage.review_status.in_(["pending", "approved"]))
            .count()
        )
        if pending_or_approved == 0:
            db.query(Moment).filter(Moment.id == item.related_id).update(
                {"status": "rejected", "review_comment": comment, "reviewed_by": admin.id, "reviewed_at": now}
            )

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
            fpath = resolve_upload_path(item.image_url, allowed_prefixes=("staging", "public"))
            if fpath.exists():
                os.remove(fpath)
            db.delete(item)
    db.commit()
    return {"deleted": len(req.ids)}


@router.get("/admin/image-preview")
def image_preview(
    request: Request,
    img_path: str = Query(..., alias="path"),
    token: str = Query(""),
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db),
):
    user = get_request_user(request, db, credentials=credentials, query_token=token)
    if not user.is_admin:
        raise HTTPException(403)

    full_path = resolve_upload_path(img_path, allowed_prefixes=("public", "staging", "verify"))
    if not full_path.exists():
        raise HTTPException(404)
    return FileResponse(full_path)


@router.get("/image")
def serve_image(
    request: Request,
    path: str = Query(...),
    token: str = Query(""),
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db),
):
    get_request_user(request, db, credentials=credentials, query_token=token)
    full_path = resolve_upload_path(path, allowed_prefixes=("public", "staging"))
    if not full_path.exists():
        raise HTTPException(404)
    return FileResponse(full_path)
