import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import Float, Integer, String, DateTime, Text, Enum, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from backend.app.core.database import Base


class ChannelType(StrEnum):
    FACE_TO_FACE = "face_to_face"
    PHONE_CALL = "phone_call"
    TEXT_MESSAGE = "text_message"
    EMAIL = "email"
    SOCIAL_MEDIA = "social_media"
    GROUP_CHAT = "group_chat"
    PUBLIC_ANNOUNCEMENT = "public_announcement"
    GOSSIP = "gossip"
    EMERGENCY_ALERT = "emergency_alert"


class MessageSentiment(StrEnum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    channel: Mapped[ChannelType] = mapped_column(Enum(ChannelType))
    topic: Mapped[str] = mapped_column(String(300), default="")
    location: Mapped[str | None] = mapped_column(String(200), nullable=True)

    participant_ids: Mapped[list] = mapped_column(JSON, default=list)
    is_active: Mapped[bool] = mapped_column(default=True)

    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    messages: Mapped[list["Message"]] = relationship(back_populates="conversation", order_by="Message.sim_timestamp")


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("conversations.id"), index=True
    )
    sender_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("citizens.id"), index=True
    )

    content: Mapped[str] = mapped_column(Text)
    sentiment: Mapped[MessageSentiment] = mapped_column(
        Enum(MessageSentiment), default=MessageSentiment.NEUTRAL
    )
    importance: Mapped[float] = mapped_column(Float, default=0.3)

    metadata_extra: Mapped[dict] = mapped_column(JSON, default=dict)

    sim_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    conversation: Mapped["Conversation"] = relationship(back_populates="messages")


class SocialMediaComment(Base):
    __tablename__ = "social_media_comments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    post_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("social_media_posts.id"), index=True
    )
    author_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("citizens.id"), index=True
    )
    content: Mapped[str] = mapped_column(Text)
    sentiment: Mapped[MessageSentiment] = mapped_column(
        Enum(MessageSentiment), default=MessageSentiment.NEUTRAL
    )
    likes: Mapped[int] = mapped_column(Integer, default=0)

    sim_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SocialMediaPost(Base):
    __tablename__ = "social_media_posts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    author_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("citizens.id"), index=True
    )
    content: Mapped[str] = mapped_column(Text)
    sentiment: Mapped[MessageSentiment] = mapped_column(
        Enum(MessageSentiment), default=MessageSentiment.NEUTRAL
    )
    likes: Mapped[int] = mapped_column(Integer, default=0)
    shares: Mapped[int] = mapped_column(Integer, default=0)
    reach: Mapped[int] = mapped_column(Integer, default=0)
    tags: Mapped[list] = mapped_column(JSON, default=list)

    sim_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
