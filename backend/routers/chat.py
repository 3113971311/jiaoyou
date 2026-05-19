import json
import os
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import or_
from sqlalchemy.orm import Session

from auth import get_admin_user, get_current_user, get_vip_user
from config import UPLOAD_DIR
from database import get_db
from models import Blacklist, ChatCallSession, Conversation, Message, User
from utils.uploads import AUDIO_EXTENSIONS, IMAGE_EXTENSIONS, VIDEO_EXTENSIONS, read_validated_upload

router = APIRouter(tags=["chat"])

ACTIVE_CALL_STATUSES = {"ringing", "active"}
MESSAGE_MEDIA_TYPES = {"image", "audio", "video", "call_audio", "call_video"}


def conversation_deleted_for_user(conv: Conversation, user_id: str) -> bool:
    if conv.user1_id == user_id:
        return bool(conv.deleted_for_user1)
    if conv.user2_id == user_id:
        return bool(conv.deleted_for_user2)
    return True


def assert_conversation_member(conv: Conversation | None, user_id: str):
    if not conv or user_id not in (conv.user1_id, conv.user2_id):
        raise HTTPException(403, "无权访问该聊天")


def other_participant_id(conv: Conversation, user_id: str) -> str:
    return conv.user2_id if conv.user1_id == user_id else conv.user1_id


def other_user_payload(conv: Conversation, user_id: str, db: Session) -> dict | None:
    other = db.query(User).filter(User.id == other_participant_id(conv, user_id)).first()
    if not other:
        return None
    return {
        "id": other.id,
        "username": other.username,
        "nickname": other.nickname,
        "avatar_url": other.avatar_url,
        "location": other.location,
    }


def parse_json_list(value: str | None) -> list:
    if not value:
        return []
    try:
        data = json.loads(value)
        return data if isinstance(data, list) else []
    except Exception:
        return []


def parse_json_object(value: str | None) -> dict:
    if not value:
        return {}
    try:
        data = json.loads(value)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def build_preview_text(message: Message | None) -> str:
    if not message:
        return ""
    preview_map = {
        "image": "[图片]",
        "audio": "[语音]",
        "video": "[视频]",
        "call_audio": "[语音通话]",
        "call_video": "[视频通话]",
    }
    if message.content_type in preview_map:
        return message.content or preview_map[message.content_type]
    return message.content or ""


def message_json(message: Message, *, include_deleted: bool = False) -> dict:
    payload = {
        "id": message.id,
        "conversation_id": message.conversation_id,
        "sender_id": message.sender_id,
        "content": message.content or "",
        "content_type": message.content_type,
        "image_url": message.image_url or "",
        "media_url": message.media_url or message.image_url or "",
        "thumbnail_url": message.thumbnail_url or "",
        "duration_seconds": message.duration_seconds,
        "call_session_id": message.call_session_id,
        "extra": parse_json_object(message.extra_json),
        "status": message.status,
        "created_at": message.created_at.isoformat() if message.created_at else None,
    }
    if include_deleted:
        payload["deleted_at"] = message.deleted_at.isoformat() if message.deleted_at else None
        payload["deleted_by_user_id"] = message.deleted_by_user_id
        payload["is_deleted"] = bool(message.deleted_at)
    return payload


def call_json(call: ChatCallSession) -> dict:
    return {
        "id": call.id,
        "conversation_id": call.conversation_id,
        "caller_id": call.caller_id,
        "callee_id": call.callee_id,
        "call_type": call.call_type,
        "status": call.status,
        "offer_sdp": call.offer_sdp or "",
        "answer_sdp": call.answer_sdp or "",
        "caller_candidates": parse_json_list(call.caller_candidates_json),
        "callee_candidates": parse_json_list(call.callee_candidates_json),
        "recording_url": call.recording_url or "",
        "recording_type": call.recording_type or "",
        "duration_seconds": call.duration_seconds,
        "started_at": call.started_at.isoformat() if call.started_at else None,
        "answered_at": call.answered_at.isoformat() if call.answered_at else None,
        "ended_at": call.ended_at.isoformat() if call.ended_at else None,
        "ended_by_user_id": call.ended_by_user_id,
        "summary_message_id": call.summary_message_id,
        "created_at": call.created_at.isoformat() if call.created_at else None,
    }


def ensure_contact_allowed(conv: Conversation, user_id: str):
    if conversation_deleted_for_user(conv, user_id):
        raise HTTPException(403, "该聊天已删除")
    if conv.contact_blocked:
        raise HTTPException(403, "删除聊天后双方将无法再次联系")


def normalize_message_payload(req: dict) -> dict:
    content_type = (req.get("content_type") or "text").strip()
    content = (req.get("content") or "").strip()
    media_url = (req.get("media_url") or req.get("image_url") or "").strip()
    thumbnail_url = (req.get("thumbnail_url") or "").strip()
    duration_seconds = req.get("duration_seconds")
    call_session_id = (req.get("call_session_id") or "").strip()
    extra = req.get("extra") if isinstance(req.get("extra"), dict) else {}

    if content_type not in {"text", "image", "audio", "video", "call_audio", "call_video"}:
        raise HTTPException(400, "不支持的消息类型")
    if content_type == "text" and not content:
        raise HTTPException(400, "消息内容不能为空")
    if content_type in MESSAGE_MEDIA_TYPES and not media_url and content_type not in {"call_audio", "call_video"}:
        raise HTTPException(400, "该消息类型缺少媒体文件")

    return {
        "content_type": content_type,
        "content": content,
        "media_url": media_url,
        "image_url": media_url if content_type == "image" else "",
        "thumbnail_url": thumbnail_url,
        "duration_seconds": int(duration_seconds) if duration_seconds else None,
        "call_session_id": call_session_id or None,
        "extra_json": json.dumps(extra, ensure_ascii=False) if extra else None,
    }


def upsert_call_summary_message(call: ChatCallSession, db: Session):
    call_label = "语音通话" if call.call_type == "audio" else "视频通话"
    status_label = {
        "ringing": "等待接听",
        "active": "通话中",
        "ended": "通话结束",
        "rejected": "已拒绝",
        "cancelled": "已取消",
        "missed": "未接听",
    }.get(call.status, "通话记录")
    duration_text = f" · {call.duration_seconds}秒" if call.duration_seconds else ""
    content = f"{call_label} {status_label}{duration_text}"
    extra = {
        "status": call.status,
        "call_type": call.call_type,
        "recording_url": call.recording_url or "",
        "duration_seconds": call.duration_seconds,
        "answered_at": call.answered_at.isoformat() if call.answered_at else None,
        "ended_at": call.ended_at.isoformat() if call.ended_at else None,
    }

    message = None
    if call.summary_message_id:
        message = db.query(Message).filter(Message.id == call.summary_message_id).first()

    if not message:
        message = Message(
            conversation_id=call.conversation_id,
            sender_id=call.caller_id,
            content=content,
            content_type=f"call_{call.call_type}",
            media_url=call.recording_url or "",
            duration_seconds=call.duration_seconds,
            call_session_id=call.id,
            extra_json=json.dumps(extra, ensure_ascii=False),
            status="sent",
        )
        db.add(message)
        db.flush()
        call.summary_message_id = message.id
    else:
        message.content = content
        message.content_type = f"call_{call.call_type}"
        message.media_url = call.recording_url or ""
        message.duration_seconds = call.duration_seconds
        message.extra_json = json.dumps(extra, ensure_ascii=False)

    conv = db.query(Conversation).filter(Conversation.id == call.conversation_id).first()
    if conv:
        conv.last_message_at = datetime.utcnow()


def append_candidate(existing_json: str | None, candidate: str) -> str:
    items = parse_json_list(existing_json)
    if candidate and candidate not in items:
        items.append(candidate)
    return json.dumps(items, ensure_ascii=False)


async def save_chat_media(file: UploadFile):
    upload = await read_validated_upload(
        file,
        max_bytes=100 * 1024 * 1024,
        allowed_kinds={"image", "audio", "video"},
        allowed_extensions=IMAGE_EXTENSIONS | AUDIO_EXTENSIONS | VIDEO_EXTENSIONS,
        fallback_extension=".bin",
        label="聊天媒体文件",
    )
    if not file.filename:
        raise HTTPException(400, "请选择文件")
    ext = upload["ext"]
    public_dir = os.path.join(UPLOAD_DIR, "public", "chat")
    os.makedirs(public_dir, exist_ok=True)
    filename = f"{uuid.uuid4()}{ext}"
    filepath = os.path.join(public_dir, filename)
    with open(filepath, "wb") as handle:
        handle.write(upload["content"])

    content_type = file.content_type or ""
    if content_type.startswith("image/"):
        kind = "image"
    elif content_type.startswith("audio/"):
        kind = "audio"
    elif content_type.startswith("video/"):
        kind = "video"
    else:
        kind = "file"

    return {"url": f"/public/chat/{filename}", "kind": upload["kind"], "content_type": upload["content_type"]}


@router.get("/conversations")
def get_conversations(cursor: str = "", limit: int = 20, user: User = Depends(get_vip_user), db: Session = Depends(get_db)):
    query = (
        db.query(Conversation)
        .filter(or_(Conversation.user1_id == user.id, Conversation.user2_id == user.id))
        .order_by(Conversation.last_message_at.desc().nullslast(), Conversation.created_at.desc())
    )
    if cursor:
        query = query.filter(Conversation.id < cursor)
    raw_items = query.limit(limit + 8).all()

    items = []
    for conv in raw_items:
        if conversation_deleted_for_user(conv, user.id):
            continue
        last_message = (
            db.query(Message)
            .filter(Message.conversation_id == conv.id, Message.deleted_at.is_(None))
            .order_by(Message.created_at.desc())
            .first()
        )
        items.append(
            {
                "id": conv.id,
                "last_message_at": conv.last_message_at.isoformat() if conv.last_message_at else None,
                "contact_blocked": bool(conv.contact_blocked),
                "other_user": other_user_payload(conv, user.id, db),
                "last_message": message_json(last_message) if last_message else None,
                "preview_text": build_preview_text(last_message) or "暂无消息",
            }
        )
        if len(items) >= limit:
            break

    next_cursor = items[-1]["id"] if len(items) == limit else None
    return {"list": items, "next_cursor": next_cursor}


@router.get("/conversations/{conv_id}/messages")
def get_messages(conv_id: str, before: str = "", limit: int = 30, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    conv = db.query(Conversation).filter(Conversation.id == conv_id).first()
    assert_conversation_member(conv, user.id)
    if conversation_deleted_for_user(conv, user.id):
        raise HTTPException(404, "该聊天已删除")

    query = (
        db.query(Message)
        .filter(Message.conversation_id == conv_id, Message.deleted_at.is_(None))
        .order_by(Message.created_at.desc())
    )
    if before:
        query = query.filter(Message.id < before)
    raw_items = query.limit(limit + 1).all()
    items = list(reversed(raw_items[:limit]))
    next_cursor = raw_items[-1].id if len(raw_items) > limit else None

    return {
        "conversation": {
            "id": conv.id,
            "contact_blocked": bool(conv.contact_blocked),
            "other_user": other_user_payload(conv, user.id, db),
        },
        "list": [message_json(message) for message in items],
        "next_cursor": next_cursor,
    }


@router.post("/conversations")
def create_conversation(req: dict, user: User = Depends(get_vip_user), db: Session = Depends(get_db)):
    target_user_id = (req.get("target_user_id") or "").strip()
    if not target_user_id or target_user_id == user.id:
        raise HTTPException(400, "请选择有效的聊天对象")

    target_user = db.query(User).filter(User.id == target_user_id, User.status == "active").first()
    if not target_user:
        raise HTTPException(404, "对方账号不存在或不可用")

    blocked = db.query(Blacklist).filter(
        or_(
            (Blacklist.blocker_id == user.id) & (Blacklist.blocked_id == target_user_id),
            (Blacklist.blocker_id == target_user_id) & (Blacklist.blocked_id == user.id),
        )
    ).first()
    if blocked:
        raise HTTPException(403, "无法与对方聊天")

    user1_id, user2_id = sorted([user.id, target_user_id])
    conv = db.query(Conversation).filter(Conversation.user1_id == user1_id, Conversation.user2_id == user2_id).first()
    if conv:
        if conv.contact_blocked:
            raise HTTPException(403, "删除聊天后双方将无法再次联系")
        if conv.deleted_for_user1 or conv.deleted_for_user2:
            conv.deleted_for_user1 = False
            conv.deleted_for_user2 = False
            db.commit()
        return {"id": conv.id}

    conv = Conversation(user1_id=user1_id, user2_id=user2_id)
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return {"id": conv.id}


@router.delete("/conversations/{conv_id}")
def delete_conversation(conv_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    conv = db.query(Conversation).filter(Conversation.id == conv_id).first()
    assert_conversation_member(conv, user.id)

    conv.deleted_for_user1 = True
    conv.deleted_for_user2 = True
    conv.contact_blocked = True
    conv.blocked_at = datetime.utcnow()
    conv.blocked_by_user_id = user.id
    db.commit()
    return {"message": "聊天已删除，双方将无法再次联系"}


@router.post("/chat/send/{conv_id}")
def send_message(conv_id: str, req: dict, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    conv = db.query(Conversation).filter(Conversation.id == conv_id).first()
    assert_conversation_member(conv, user.id)
    ensure_contact_allowed(conv, user.id)

    payload = normalize_message_payload(req)
    message = Message(
        conversation_id=conv_id,
        sender_id=user.id,
        content=payload["content"],
        content_type=payload["content_type"],
        image_url=payload["image_url"],
        media_url=payload["media_url"],
        thumbnail_url=payload["thumbnail_url"],
        duration_seconds=payload["duration_seconds"],
        call_session_id=payload["call_session_id"],
        extra_json=payload["extra_json"],
        status="sent",
    )
    db.add(message)
    conv.last_message_at = datetime.utcnow()
    db.commit()
    db.refresh(message)
    return message_json(message)


@router.delete("/conversations/{conv_id}/messages/{message_id}")
def delete_message(conv_id: str, message_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    conv = db.query(Conversation).filter(Conversation.id == conv_id).first()
    assert_conversation_member(conv, user.id)
    ensure_contact_allowed(conv, user.id)

    message = db.query(Message).filter(Message.id == message_id, Message.conversation_id == conv_id).first()
    if not message:
        raise HTTPException(404, "消息不存在")
    if message.sender_id != user.id:
        raise HTTPException(403, "只能删除自己发送的消息")

    message.deleted_at = datetime.utcnow()
    message.deleted_by_user_id = user.id
    db.commit()
    return {"message": "消息已删除"}


@router.post("/upload/chat-media")
async def upload_chat_media(file: UploadFile = File(...), user: User = Depends(get_current_user)):
    return await save_chat_media(file)


@router.post("/upload/chat-image")
async def upload_chat_image(file: UploadFile = File(...), user: User = Depends(get_current_user)):
    result = await save_chat_media(file)
    if result["kind"] not in {"image", "audio", "video"}:
        raise HTTPException(400, "不支持的文件类型")
    return result


@router.get("/conversations/{conv_id}/active-call")
def get_active_call(conv_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    conv = db.query(Conversation).filter(Conversation.id == conv_id).first()
    assert_conversation_member(conv, user.id)
    ensure_contact_allowed(conv, user.id)

    call = (
        db.query(ChatCallSession)
        .filter(ChatCallSession.conversation_id == conv_id, ChatCallSession.status.in_(list(ACTIVE_CALL_STATUSES)))
        .order_by(ChatCallSession.created_at.desc())
        .first()
    )
    return {"call": call_json(call) if call else None}


@router.post("/conversations/{conv_id}/calls")
def create_call(conv_id: str, req: dict, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    conv = db.query(Conversation).filter(Conversation.id == conv_id).first()
    assert_conversation_member(conv, user.id)
    ensure_contact_allowed(conv, user.id)

    active_call = (
        db.query(ChatCallSession)
        .filter(ChatCallSession.conversation_id == conv_id, ChatCallSession.status.in_(list(ACTIVE_CALL_STATUSES)))
        .order_by(ChatCallSession.created_at.desc())
        .first()
    )
    if active_call:
        raise HTTPException(409, "当前已有进行中的通话")

    call_type = (req.get("call_type") or "audio").strip()
    if call_type not in {"audio", "video"}:
        raise HTTPException(400, "不支持的通话类型")

    call = ChatCallSession(
        conversation_id=conv_id,
        caller_id=user.id,
        callee_id=other_participant_id(conv, user.id),
        call_type=call_type,
        status="ringing",
        caller_candidates_json="[]",
        callee_candidates_json="[]",
        started_at=datetime.utcnow(),
    )
    db.add(call)
    db.commit()
    db.refresh(call)
    return call_json(call)


@router.get("/calls/{call_id}")
def get_call(call_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    call = db.query(ChatCallSession).filter(ChatCallSession.id == call_id).first()
    if not call:
        raise HTTPException(404, "通话不存在")
    conv = db.query(Conversation).filter(Conversation.id == call.conversation_id).first()
    assert_conversation_member(conv, user.id)
    return call_json(call)


@router.post("/calls/{call_id}/signal")
def update_call_signal(call_id: str, req: dict, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    call = db.query(ChatCallSession).filter(ChatCallSession.id == call_id).first()
    if not call:
        raise HTTPException(404, "通话不存在")
    conv = db.query(Conversation).filter(Conversation.id == call.conversation_id).first()
    assert_conversation_member(conv, user.id)

    signal_type = (req.get("type") or "").strip()
    payload = req.get("payload")
    if signal_type not in {"offer", "answer", "ice"}:
        raise HTTPException(400, "不支持的信令类型")

    if signal_type == "offer":
        if user.id != call.caller_id:
            raise HTTPException(403, "只有发起方可以发送 offer")
        call.offer_sdp = str(payload or "")
    elif signal_type == "answer":
        if user.id != call.callee_id:
            raise HTTPException(403, "只有接听方可以发送 answer")
        call.answer_sdp = str(payload or "")
        if call.status == "ringing":
            call.status = "active"
            call.answered_at = datetime.utcnow()
    else:
        candidate = str(payload or "").strip()
        if user.id == call.caller_id:
            call.caller_candidates_json = append_candidate(call.caller_candidates_json, candidate)
        elif user.id == call.callee_id:
            call.callee_candidates_json = append_candidate(call.callee_candidates_json, candidate)

    db.commit()
    db.refresh(call)
    return call_json(call)


@router.post("/calls/{call_id}/accept")
def accept_call(call_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    call = db.query(ChatCallSession).filter(ChatCallSession.id == call_id).first()
    if not call:
        raise HTTPException(404, "通话不存在")
    if user.id != call.callee_id:
        raise HTTPException(403, "只有接听方可以操作")
    if call.status not in {"ringing", "active"}:
        raise HTTPException(400, "当前通话不可接听")

    call.status = "active"
    call.answered_at = call.answered_at or datetime.utcnow()
    db.commit()
    db.refresh(call)
    return call_json(call)


@router.post("/calls/{call_id}/reject")
def reject_call(call_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    call = db.query(ChatCallSession).filter(ChatCallSession.id == call_id).first()
    if not call:
        raise HTTPException(404, "通话不存在")
    if user.id != call.callee_id:
        raise HTTPException(403, "只有接听方可以拒绝")

    call.status = "rejected"
    call.ended_at = datetime.utcnow()
    call.ended_by_user_id = user.id
    upsert_call_summary_message(call, db)
    db.commit()
    db.refresh(call)
    return call_json(call)


@router.post("/calls/{call_id}/end")
def end_call(call_id: str, req: dict, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    call = db.query(ChatCallSession).filter(ChatCallSession.id == call_id).first()
    if not call:
        raise HTTPException(404, "通话不存在")
    conv = db.query(Conversation).filter(Conversation.id == call.conversation_id).first()
    assert_conversation_member(conv, user.id)

    if call.status in {"ended", "rejected", "cancelled", "missed"}:
        return call_json(call)

    requested_status = (req.get("status") or "").strip()
    if requested_status not in {"ended", "cancelled", "missed"}:
        requested_status = "ended" if call.status == "active" else "cancelled"

    call.status = requested_status
    call.ended_at = datetime.utcnow()
    call.ended_by_user_id = user.id
    upsert_call_summary_message(call, db)
    db.commit()
    db.refresh(call)
    return call_json(call)


@router.post("/calls/{call_id}/recording")
def attach_call_recording(call_id: str, req: dict, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    call = db.query(ChatCallSession).filter(ChatCallSession.id == call_id).first()
    if not call:
        raise HTTPException(404, "通话不存在")
    conv = db.query(Conversation).filter(Conversation.id == call.conversation_id).first()
    assert_conversation_member(conv, user.id)

    media_url = (req.get("media_url") or "").strip()
    if not media_url:
        raise HTTPException(400, "录音或录像地址不能为空")

    call.recording_url = media_url
    call.recording_type = (req.get("recording_type") or call.call_type).strip() or call.call_type
    duration_seconds = req.get("duration_seconds")
    call.duration_seconds = int(duration_seconds) if duration_seconds else call.duration_seconds
    if call.status == "active":
        call.status = "ended"
    call.ended_at = call.ended_at or datetime.utcnow()
    upsert_call_summary_message(call, db)
    db.commit()
    db.refresh(call)
    return call_json(call)


@router.get("/admin/chats")
def admin_chat_list(search: str = "", admin: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    conversations = (
        db.query(Conversation)
        .order_by(Conversation.last_message_at.desc().nullslast(), Conversation.created_at.desc())
        .limit(200)
        .all()
    )
    result = []
    for conv in conversations:
        user1 = db.query(User).filter(User.id == conv.user1_id).first()
        user2 = db.query(User).filter(User.id == conv.user2_id).first()

        if search:
            haystack = " ".join(
                [
                    conv.user1_id,
                    conv.user2_id,
                    user1.username if user1 else "",
                    user1.nickname if user1 else "",
                    user2.username if user2 else "",
                    user2.nickname if user2 else "",
                ]
            ).lower()
            if search.lower() not in haystack:
                continue

        last_message = db.query(Message).filter(Message.conversation_id == conv.id).order_by(Message.created_at.desc()).first()
        result.append(
            {
                "id": conv.id,
                "user1_id": conv.user1_id,
                "user2_id": conv.user2_id,
                "user1_name": (user1.nickname or user1.username) if user1 else conv.user1_id,
                "user2_name": (user2.nickname or user2.username) if user2 else conv.user2_id,
                "last_message_at": conv.last_message_at.isoformat() if conv.last_message_at else None,
                "contact_blocked": bool(conv.contact_blocked),
                "deleted_for_user1": bool(conv.deleted_for_user1),
                "deleted_for_user2": bool(conv.deleted_for_user2),
                "last_message": message_json(last_message, include_deleted=True) if last_message else None,
                "preview_text": build_preview_text(last_message) or "暂无消息",
            }
        )
    return result


@router.get("/admin/chats/{conv_id}/messages")
def admin_chat_messages(conv_id: str, admin: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    messages = (
        db.query(Message)
        .filter(Message.conversation_id == conv_id)
        .order_by(Message.created_at.desc())
        .limit(200)
        .all()
    )
    items = []
    for message in reversed(messages):
        payload = message_json(message, include_deleted=True)
        sender = db.query(User).filter(User.id == message.sender_id).first()
        payload["sender_name"] = (sender.nickname or sender.username) if sender else message.sender_id
        items.append(payload)
    return items


@router.get("/admin/chats/{conv_id}/calls")
def admin_chat_calls(conv_id: str, admin: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    calls = (
        db.query(ChatCallSession)
        .filter(ChatCallSession.conversation_id == conv_id)
        .order_by(ChatCallSession.created_at.desc())
        .limit(100)
        .all()
    )
    return [call_json(call) for call in calls]
