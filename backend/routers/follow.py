from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Follow, Notification, User
from auth import get_current_user, get_vip_user
from datetime import datetime

router = APIRouter(tags=["follow"])

@router.post("/follow/{target_id}")
def follow_user(target_id: str, user: User = Depends(get_vip_user), db: Session = Depends(get_db)):
    if user.id == target_id: raise HTTPException(400)
    target = db.query(User).filter(User.id == target_id).first()
    if not target: raise HTTPException(404)
    existing = db.query(Follow).filter(Follow.follower_id == user.id, Follow.followed_id == target_id).first()
    if existing: return {"message": "已关注", "mutual": False}
    db.add(Follow(follower_id=user.id, followed_id=target_id))
    # 通知
    db.add(Notification(user_id=target_id, type="followed", title="新粉丝", content=f"{user.nickname or user.username} 关注了你"))
    db.commit()
    # 互关检查
    mutual = db.query(Follow).filter(Follow.follower_id == target_id, Follow.followed_id == user.id).first()
    return {"message": "关注成功", "mutual": bool(mutual)}

@router.delete("/follow/{target_id}")
def unfollow_user(target_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db.query(Follow).filter(Follow.follower_id == user.id, Follow.followed_id == target_id).delete()
    db.commit()
    return {"message": "已取消关注"}

@router.get("/follow/following")
def get_following(cursor: str = "", limit: int = 20, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    items = db.query(User).join(Follow, Follow.followed_id == User.id).filter(Follow.follower_id == user.id).limit(limit+1).all()
    return {"list": [{"id": u.id, "username": u.username, "nickname": u.nickname, "avatar_url": u.avatar_url} for u in items[:limit]],
            "next_cursor": items[limit].id if len(items) > limit else None}

@router.get("/follow/followers")
def get_followers(cursor: str = "", limit: int = 20, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    items = db.query(User).join(Follow, Follow.follower_id == User.id).filter(Follow.followed_id == user.id).limit(limit+1).all()
    return {"list": [{"id": u.id, "username": u.username, "nickname": u.nickname, "avatar_url": u.avatar_url} for u in items[:limit]],
            "next_cursor": items[limit].id if len(items) > limit else None}

@router.get("/follow/status/{target_id}")
def follow_status(target_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    i_follow = db.query(Follow).filter(Follow.follower_id == user.id, Follow.followed_id == target_id).first()
    they_follow = db.query(Follow).filter(Follow.follower_id == target_id, Follow.followed_id == user.id).first()
    return {"i_follow": bool(i_follow), "they_follow": bool(they_follow), "mutual": bool(i_follow and they_follow)}
