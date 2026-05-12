from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import engine
from sqlalchemy.orm import declarative_base

Base = declarative_base()

def generate_uuid():
    import uuid
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=generate_uuid)
    username = Column(String(30), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    nickname = Column(String(50))
    avatar_url = Column(String(500))
    avatar_staging = Column(String(500))
    gender = Column(String(10))
    birthday = Column(DateTime)
    bio = Column(Text)
    location = Column(String(100))
    vip_expires_at = Column(DateTime)
    warning_count = Column(Integer, default=0)
    is_admin = Column(Boolean, default=False)
    status = Column(String(20), default="active")
    # 实名认证
    real_name = Column(String(50))
    id_card = Column(String(18))
    id_photo = Column(String(500))
    is_verified = Column(Boolean, default=False)
    verify_status = Column(String(20), default="")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete")
    moments = relationship("Moment", back_populates="user", cascade="all, delete")
    sent_messages = relationship("Message", back_populates="sender_view", foreign_keys="Message.sender_id", cascade="all, delete")
    vip_orders = relationship("VipOrder", back_populates="user", cascade="all, delete")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete")
    warnings = relationship("Warning", back_populates="user_rel", foreign_keys="Warning.user_id", cascade="all, delete")


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token_hash = Column(String(255), unique=True)
    family = Column(String, nullable=False)
    expires_at = Column(DateTime)
    revoked = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="refresh_tokens")


class Follow(Base):
    __tablename__ = "follows"
    id = Column(String, primary_key=True, default=generate_uuid)
    follower_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    followed_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (UniqueConstraint("follower_id", "followed_id"),)


class Conversation(Base):
    __tablename__ = "conversations"
    id = Column(String, primary_key=True, default=generate_uuid)
    user1_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    user2_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    last_message_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (UniqueConstraint("user1_id", "user2_id"),)


class Message(Base):
    __tablename__ = "messages"
    id = Column(String, primary_key=True, default=generate_uuid)
    conversation_id = Column(String, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    sender_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    content = Column(Text)
    content_type = Column(String(20), default="text")
    image_url = Column(String(500))
    status = Column(String(20), default="sent")
    created_at = Column(DateTime, server_default=func.now())

    conversation = relationship("Conversation", backref="messages")
    sender_view = relationship("User", back_populates="sent_messages", foreign_keys=[sender_id])


class Moment(Base):
    __tablename__ = "moments"
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    content_text = Column(Text)
    status = Column(String(20), default="pending_review")
    review_comment = Column(Text)
    reviewed_by = Column(String)
    reviewed_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="moments")
    images = relationship("MomentImage", back_populates="moment", cascade="all, delete")
    likes = relationship("MomentLike", back_populates="moment", cascade="all, delete")
    comments = relationship("MomentComment", back_populates="moment", cascade="all, delete")
    favorites = relationship("MomentFavorite", back_populates="moment", cascade="all, delete")


class MomentImage(Base):
    __tablename__ = "moment_images"
    id = Column(String, primary_key=True, default=generate_uuid)
    moment_id = Column(String, ForeignKey("moments.id", ondelete="CASCADE"), nullable=False)
    image_url = Column(String(500))
    thumbnail_url = Column(String(500))
    public_url = Column(String(500))
    review_status = Column(String(20), default="pending")
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())

    moment = relationship("Moment", back_populates="images")


class MomentLike(Base):
    __tablename__ = "moment_likes"
    id = Column(String, primary_key=True, default=generate_uuid)
    moment_id = Column(String, ForeignKey("moments.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    moment = relationship("Moment", back_populates="likes")
    __table_args__ = (UniqueConstraint("moment_id", "user_id"),)


class MomentComment(Base):
    __tablename__ = "moment_comments"
    id = Column(String, primary_key=True, default=generate_uuid)
    moment_id = Column(String, ForeignKey("moments.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    moment = relationship("Moment", back_populates="comments")


class MomentFavorite(Base):
    __tablename__ = "moment_favorites"
    id = Column(String, primary_key=True, default=generate_uuid)
    moment_id = Column(String, ForeignKey("moments.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    moment = relationship("Moment", back_populates="favorites")
    __table_args__ = (UniqueConstraint("moment_id", "user_id"),)


class ReviewQueue(Base):
    __tablename__ = "review_queue"
    id = Column(String, primary_key=True, default=generate_uuid)
    image_url = Column(String(500))
    thumbnail_url = Column(String(500))
    image_type = Column(String(20))
    related_id = Column(String)
    submitted_by = Column(String, ForeignKey("users.id", ondelete="CASCADE"))
    status = Column(String(20), default="pending")
    reviewed_by = Column(String)
    review_comment = Column(Text)
    submitted_at = Column(DateTime, server_default=func.now())
    reviewed_at = Column(DateTime)


class MatchQueue(Base):
    __tablename__ = "match_queue"
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    scope = Column(String(10))
    city = Column(String(50))
    province = Column(String(50))
    latitude = Column(Float)
    longitude = Column(Float)
    prefer_gender = Column(String(10))
    status = Column(String(20), default="waiting")
    matched_with = Column(String)
    matched_at = Column(DateTime)
    expires_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())


class MatchDailyCount(Base):
    __tablename__ = "match_daily_count"
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"))
    date = Column(DateTime)
    count = Column(Integer, default=0)
    __table_args__ = (UniqueConstraint("user_id", "date"),)


class CardBatch(Base):
    __tablename__ = "card_batches"
    id = Column(String, primary_key=True, default=generate_uuid)
    batch_name = Column(String(100))
    denomination_days = Column(Integer, nullable=False)
    expire_days = Column(Integer, default=7)
    quantity = Column(Integer, nullable=False)
    generated_by = Column(String, ForeignKey("users.id"))
    note = Column(Text)
    created_at = Column(DateTime, server_default=func.now())


class Card(Base):
    __tablename__ = "cards"
    id = Column(String, primary_key=True, default=generate_uuid)
    batch_id = Column(String, ForeignKey("card_batches.id"), nullable=False)
    card_code = Column(String(50), unique=True, nullable=False)
    code_hash = Column(String(64), nullable=False)
    denomination_days = Column(Integer, nullable=False)
    status = Column(String(20), default="unused")
    used_by = Column(String)
    used_at = Column(DateTime)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, server_default=func.now())


class VipOrder(Base):
    __tablename__ = "vip_orders"
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    card_id = Column(String)
    days = Column(Integer, nullable=False)
    order_type = Column(String(20), nullable=False)
    vip_before = Column(DateTime)
    vip_after = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="vip_orders")


class PaymentOrder(Base):
    __tablename__ = "payment_orders"
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    plan_days = Column(Integer, nullable=False)
    amount = Column(Float, nullable=False)
    email = Column(String(255), nullable=False)
    payment_method = Column(String(20), nullable=False)
    trade_no = Column(String(100))
    status = Column(String(20), default="pending")
    card_code = Column(String(50))
    created_at = Column(DateTime, server_default=func.now())
    paid_at = Column(DateTime)


class Report(Base):
    __tablename__ = "reports"
    id = Column(String, primary_key=True, default=generate_uuid)
    reporter_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"))
    target_type = Column(String(20))
    target_id = Column(String)
    reason = Column(Text)
    status = Column(String(20), default="pending")
    handled_by = Column(String)
    result = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    handled_at = Column(DateTime)


class Warning(Base):
    __tablename__ = "warnings"
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    warned_by = Column(String, ForeignKey("users.id"))
    reason = Column(Text)
    related_chat_image_url = Column(String(500))
    created_at = Column(DateTime, server_default=func.now())

    user_rel = relationship("User", back_populates="warnings", foreign_keys=[user_id])


class Blacklist(Base):
    __tablename__ = "blacklists"
    id = Column(String, primary_key=True, default=generate_uuid)
    blocker_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    blocked_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    __table_args__ = (UniqueConstraint("blocker_id", "blocked_id"),)


class Notification(Base):
    __tablename__ = "notifications"
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    type = Column(String(30))
    title = Column(String(200))
    content = Column(Text)
    related_id = Column(String)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="notifications")


class SensitiveWord(Base):
    __tablename__ = "sensitive_words"
    id = Column(String, primary_key=True, default=generate_uuid)
    word = Column(String(100), unique=True)
    level = Column(String(10))
    created_by = Column(String)
    created_at = Column(DateTime, server_default=func.now())


class SiteConfig(Base):
    __tablename__ = "site_configs"
    config_key = Column(String(50), primary_key=True)
    config_value = Column(Text)
    value_type = Column(String(10), default="text")
    description = Column(String(200))
    updated_by = Column(String)
    updated_at = Column(DateTime, server_default=func.now())


def init_db():
    Base.metadata.create_all(bind=engine)
