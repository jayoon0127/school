from datetime import datetime, UTC
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import UniqueConstraint, CheckConstraint, or_
from . import db

def now_utc():
    return datetime.now(UTC)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), unique=True, nullable=False, index=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    grade = db.Column(db.Integer, nullable=True)
    role = db.Column(db.String(20), nullable=False, default="student")
    is_active_user = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime(timezone=True), default=now_utc, nullable=False)

    posts = db.relationship("Post", backref="author", lazy=True)
    comments = db.relationship("Comment", backref="author", lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        return self.role in {"admin", "superadmin"}

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    board = db.Column(db.String(20), nullable=False, index=True)
    category = db.Column(db.String(20), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False, index=True)
    content = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    is_deleted = db.Column(db.Boolean, nullable=False, default=False)
    is_hidden = db.Column(db.Boolean, nullable=False, default=False)
    is_pinned = db.Column(db.Boolean, nullable=False, default=False)
    view_count = db.Column(db.Integer, nullable=False, default=0)
    like_count = db.Column(db.Integer, nullable=False, default=0)
    dislike_count = db.Column(db.Integer, nullable=False, default=0)
    comment_count = db.Column(db.Integer, nullable=False, default=0)
    hot_score = db.Column(db.Integer, nullable=False, default=0, index=True)
    created_at = db.Column(db.DateTime(timezone=True), default=now_utc, nullable=False, index=True)
    updated_at = db.Column(db.DateTime(timezone=True), default=now_utc, onupdate=now_utc, nullable=False)

    attachments = db.relationship("Attachment", backref="post", cascade="all, delete-orphan", lazy=True)
    comments = db.relationship("Comment", backref="post", cascade="all, delete-orphan", lazy=True)
    reactions = db.relationship("Reaction", backref="post", cascade="all, delete-orphan", lazy=True)

    def recalc_hot_score(self):
        self.hot_score = (self.like_count * 3) + (self.comment_count * 2) + min(self.view_count // 10, 200)

    @property
    def is_hot(self):
        return self.hot_score >= 30 and not self.is_deleted and not self.is_hidden

class Attachment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey("post.id"), nullable=False, index=True)
    file_name = db.Column(db.String(255), nullable=False)
    stored_name = db.Column(db.String(255), nullable=False)
    mime_type = db.Column(db.String(100), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)
    media_type = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=now_utc, nullable=False)

class Reaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey("post.id"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    reaction_type = db.Column(db.String(10), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=now_utc, nullable=False)

    __table_args__ = (
        UniqueConstraint("post_id", "user_id", name="uq_post_user_reaction"),
        CheckConstraint("reaction_type IN ('like', 'dislike')", name="ck_reaction_type"),
    )

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey("post.id"), nullable=False, index=True)
    author_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    parent_id = db.Column(db.Integer, db.ForeignKey("comment.id"), nullable=True, index=True)
    content = db.Column(db.Text, nullable=False)
    is_deleted = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime(timezone=True), default=now_utc, nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), default=now_utc, onupdate=now_utc, nullable=False)

class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reporter_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    target_type = db.Column(db.String(20), nullable=False)
    target_post_id = db.Column(db.Integer, db.ForeignKey("post.id"), nullable=True)
    target_comment_id = db.Column(db.Integer, db.ForeignKey("comment.id"), nullable=True)
    reason = db.Column(db.String(50), nullable=False)
    detail = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), nullable=False, default="pending")
    created_at = db.Column(db.DateTime(timezone=True), default=now_utc, nullable=False)
    handled_by = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    handled_at = db.Column(db.DateTime(timezone=True), nullable=True)

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    kind = db.Column(db.String(30), nullable=False)
    message = db.Column(db.String(255), nullable=False)
    link = db.Column(db.String(255), nullable=True)
    is_read = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime(timezone=True), default=now_utc, nullable=False)

class Ban(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    ban_type = db.Column(db.String(20), nullable=False)
    reason = db.Column(db.String(100), nullable=False)
    note = db.Column(db.Text, nullable=True)
    starts_at = db.Column(db.DateTime(timezone=True), default=now_utc, nullable=False)
    ends_at = db.Column(db.DateTime(timezone=True), nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=now_utc, nullable=False)
    active = db.Column(db.Boolean, nullable=False, default=True)

    @classmethod
    def active_for_user(cls, user_id):
        current = now_utc()
        return cls.query.filter(
            cls.user_id == user_id,
            cls.active == True,
            cls.starts_at <= current,
            or_(cls.ends_at.is_(None), cls.ends_at > current),
        ).order_by(cls.created_at.desc()).first()

class IPBan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ip_address = db.Column(db.String(64), nullable=False, unique=True, index=True)
    reason = db.Column(db.String(100), nullable=False)
    note = db.Column(db.Text, nullable=True)
    starts_at = db.Column(db.DateTime(timezone=True), default=now_utc, nullable=False)
    ends_at = db.Column(db.DateTime(timezone=True), nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=now_utc, nullable=False)
    active = db.Column(db.Boolean, nullable=False, default=True)

    @classmethod
    def active_for_ip(cls, ip_address):
        current = now_utc()
        return cls.query.filter(
            cls.ip_address == ip_address,
            cls.active == True,
            cls.starts_at <= current,
            or_(cls.ends_at.is_(None), cls.ends_at > current),
        ).first()