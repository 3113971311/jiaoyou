from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, ForeignKey, UniqueConstraint, Index, inspect
from sqlalchemy.orm import Session, relationship
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
    last_located_at = Column(DateTime)
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


class VipPlan(Base):
    __tablename__ = "vip_plans"
    id = Column(String, primary_key=True, default=generate_uuid)
    days = Column(Integer, unique=True, nullable=False)
    price = Column(Float, nullable=False)
    title = Column(String(50))
    description = Column(String(200))
    badge = Column(String(20))
    payment_qr_url = Column(String(500))
    first_discount_rate = Column(Float, default=0)
    first_discount_qr_url = Column(String(500))
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())


class PaymentOrder(Base):
    __tablename__ = "payment_orders"
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    plan_days = Column(Integer, nullable=False)
    amount = Column(Float, nullable=False)
    original_amount = Column(Float)
    discount_rate = Column(Float, default=0)
    is_first_discount = Column(Boolean, default=False)
    email = Column(String(255), nullable=False)
    payment_method = Column(String(20), nullable=False)
    trade_no = Column(String(100))
    payment_qr_url = Column(String(500))
    submitted_order_no = Column(String(100))
    verification_message = Column(Text)
    verified_bill_id = Column(String)
    last_checked_at = Column(DateTime)
    status = Column(String(20), default="pending")
    card_code = Column(String(50))
    created_at = Column(DateTime, server_default=func.now())
    paid_at = Column(DateTime)


class AlipayBill(Base):
    __tablename__ = "alipay_bills"
    id = Column(String, primary_key=True)
    trade_no = Column(String(100), index=True)
    order_no = Column(String(100), index=True)
    amount = Column(Float, index=True)
    amount_text = Column(String(50))
    posted_at = Column(DateTime, index=True)
    accounting_type = Column(String(50))
    biz_description = Column(String(200))
    payment_memo = Column(Text)
    remark = Column(Text)
    counterparty = Column(String(200))
    operation = Column(String(50))
    source = Column(String(500))
    raw_json = Column(Text)
    captured_at = Column(DateTime)
    issue_status = Column(String(20), default="pending", index=True)
    consumed_by_order_id = Column(String, index=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())


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


DEFAULT_VIP_PLANS = [
    {"days": 7, "price": 9.9, "title": "7 天 VIP", "description": "体验套餐", "badge": "试用", "sort_order": 10},
    {"days": 30, "price": 29.9, "title": "30 天 VIP", "description": "月度套餐", "badge": "热门", "sort_order": 20},
    {"days": 90, "price": 69.9, "title": "90 天 VIP", "description": "季度套餐", "badge": "", "sort_order": 30},
    {"days": 180, "price": 119.9, "title": "180 天 VIP", "description": "半年套餐", "badge": "", "sort_order": 40},
    {"days": 360, "price": 199.9, "title": "360 天 VIP", "description": "年度套餐", "badge": "最值", "sort_order": 50},
]

def seed_default_vip_plans():
    with Session(engine) as db:
        if db.query(VipPlan).count() > 0:
            return
        for item in DEFAULT_VIP_PLANS:
            db.add(VipPlan(**item))
        db.commit()

def ensure_payment_order_columns():
    existing = {col["name"] for col in inspect(engine).get_columns("payment_orders")}
    wanted = {
        "original_amount": "FLOAT",
        "discount_rate": "FLOAT DEFAULT 0",
        "is_first_discount": "BOOLEAN DEFAULT 0",
        "payment_qr_url": "TEXT",
        "submitted_order_no": "TEXT",
        "verification_message": "TEXT",
        "verified_bill_id": "TEXT",
        "last_checked_at": "DATETIME",
    }
    with engine.begin() as conn:
        for name, ddl in wanted.items():
            if name not in existing:
                conn.exec_driver_sql(f"ALTER TABLE payment_orders ADD COLUMN {name} {ddl}")


def ensure_vip_plan_columns():
    existing = {col["name"] for col in inspect(engine).get_columns("vip_plans")}
    wanted = {
        "payment_qr_url": "TEXT",
        "first_discount_rate": "FLOAT DEFAULT 0",
        "first_discount_qr_url": "TEXT",
    }
    with engine.begin() as conn:
        for name, ddl in wanted.items():
            if name not in existing:
                conn.exec_driver_sql(f"ALTER TABLE vip_plans ADD COLUMN {name} {ddl}")


def ensure_alipay_bill_columns():
    existing = {col["name"] for col in inspect(engine).get_columns("alipay_bills")}
    wanted = {
        "issue_status": "TEXT DEFAULT 'pending'",
    }
    with engine.begin() as conn:
        for name, ddl in wanted.items():
            if name not in existing:
                conn.exec_driver_sql(f"ALTER TABLE alipay_bills ADD COLUMN {name} {ddl}")
        if "issue_status" in existing or "issue_status" in wanted:
            conn.exec_driver_sql("UPDATE alipay_bills SET issue_status = 'pending' WHERE issue_status IS NULL OR issue_status = ''")


def init_db():
    Base.metadata.create_all(bind=engine)
    ensure_vip_plan_columns()
    ensure_payment_order_columns()
    ensure_alipay_bill_columns()
    seed_default_vip_plans()
