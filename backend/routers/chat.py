from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy.orm import Session
from database import get_db
from models import Conversation, Message, Blacklist, User
from auth import get_current_user, get_vip_user, get_admin_user
import os, uuid
from config import UPLOAD_DIR
from datetime import datetime

router = APIRouter(tags=["chat"])

@router.get("/conversations")
def get_convs(cursor: str = "", limit: int = 20, user: User = Depends(get_vip_user), db: Session = Depends(get_db)):
    q = db.query(Conversation).filter((Conversation.user1_id == user.id) | (Conversation.user2_id == user.id)).order_by(Conversation.last_message_at.desc().nullslast())
    if cursor: q = q.filter(Conversation.id < cursor)
    items = q.limit(limit + 1).all()
    result = []
    for c in items[:limit]:
        other_id = c.user2_id if c.user1_id == user.id else c.user1_id
        other = db.query(User).filter(User.id == other_id).first()
        last_msg = db.query(Message).filter(Message.conversation_id == c.id).order_by(Message.created_at.desc()).first()
        result.append({"id": c.id, "last_message_at": c.last_message_at.isoformat() if c.last_message_at else None,
                "other_user": {"id": other.id if other else "", "username": other.username if other else "", "nickname": other.nickname if other else "", "avatar_url": other.avatar_url if other else None} if other else None,
                "last_message": {"content": last_msg.content, "created_at": last_msg.created_at.isoformat()} if last_msg else None})
    return {"list": result, "next_cursor": items[limit-1].id if len(items) > limit else None}

@router.get("/conversations/{conv_id}/messages")
def get_messages(conv_id: str, before: str = "", limit: int = 30, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    conv = db.query(Conversation).filter(Conversation.id == conv_id).first()
    if not conv or (conv.user1_id != user.id and conv.user2_id != user.id):
        raise HTTPException(403)
    q = db.query(Message).filter(Message.conversation_id == conv_id).order_by(Message.created_at.desc())
    if before: q = q.filter(Message.id < before)
    items = q.limit(limit + 1).all()
    return {"list": [{"id": m.id, "sender_id": m.sender_id, "content": m.content, "content_type": m.content_type, "image_url": m.image_url, "created_at": m.created_at.isoformat()} for m in reversed(items[:limit])]}

@router.post("/conversations")
def create_conv(req: dict, user: User = Depends(get_vip_user), db: Session = Depends(get_db)):
    target = req.get("target_user_id")
    if db.query(Blacklist).filter((Blacklist.blocker_id == user.id) & (Blacklist.blocked_id == target) | (Blacklist.blocker_id == target) & (Blacklist.blocked_id == user.id)).first():
        raise HTTPException(403, "无法与对方聊天")
    a, b = sorted([user.id, target])
    conv = db.query(Conversation).filter(Conversation.user1_id == a, Conversation.user2_id == b).first()
    if not conv:
        conv = Conversation(user1_id=a, user2_id=b)
        db.add(conv); db.commit()
    return {"id": conv.id}

@router.post("/chat/send/{conv_id}")
def send_message(conv_id: str, req: dict, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    conv = db.query(Conversation).filter(Conversation.id == conv_id).first()
    if not conv or (conv.user1_id != user.id and conv.user2_id != user.id):
        raise HTTPException(403)
    m = Message(conversation_id=conv_id, sender_id=user.id, content=req.get("content"), content_type=req.get("content_type","text"), image_url=req.get("image_url"))
    db.add(m)
    from datetime import datetime
    conv.last_message_at = datetime.utcnow()
    db.commit()
    return {"id":m.id,"sender_id":m.sender_id,"content":m.content,"content_type":m.content_type,"image_url":m.image_url,"created_at":m.created_at.isoformat()}

@router.post("/upload/chat-image")
async def upload_chat_img(file: UploadFile, user: User = Depends(get_current_user)):
    ext = os.path.splitext(file.filename)[1] or ".jpg"
    fname = f"{uuid.uuid4()}{ext}"
    public_dir = os.path.join(UPLOAD_DIR, "public", "chat")
    os.makedirs(public_dir, exist_ok=True)
    fpath = os.path.join(public_dir, fname)
    with open(fpath, "wb") as f: f.write(await file.read())
    return {"url": f"/public/chat/{fname}"}

# Admin chat monitor
@router.get("/admin/chats")
def admin_chats(search: str = "", admin: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    q = db.query(Conversation)
    if search:
        q = q.join(User, (User.id == Conversation.user1_id) | (User.id == Conversation.user2_id)).filter(User.username.contains(search))
    items = q.order_by(Conversation.last_message_at.desc().nullslast()).limit(50).all()
    return [{"id": c.id, "user1_id": c.user1_id, "user2_id": c.user2_id, "last_message_at": c.last_message_at.isoformat() if c.last_message_at else None} for c in items]

@router.get("/admin/chats/{conv_id}/messages")
def admin_chat_msgs(conv_id: str, admin: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    msgs = db.query(Message).filter(Message.conversation_id == conv_id).order_by(Message.created_at.desc()).limit(50).all()
    return list(reversed([{"id": m.id, "sender_id": m.sender_id, "content": m.content, "content_type": m.content_type, "image_url": m.image_url, "created_at": m.created_at.isoformat()} for m in msgs]))
