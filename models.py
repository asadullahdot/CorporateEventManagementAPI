"""SQLAlchemy database models for events and their registrations."""

import datetime as dt
from typing import List

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db import Base


class Event(Base):
    """A corporate event that employees can register for."""

    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    date: Mapped[dt.date] = mapped_column(Date, nullable=False)
    location: Mapped[str] = mapped_column(String(200), nullable=False)
    max_capacity: Mapped[int] = mapped_column(Integer, nullable=False)

    registrations: Mapped[List["Registration"]] = relationship(
        back_populates="event", cascade="all, delete-orphan"
    )


class Registration(Base):
    """An employee's registration for a single event."""

    __tablename__ = "registrations"
    # Backstop for the duplicate rule (also checked in services.py).
    __table_args__ = (UniqueConstraint("event_id", "attendee_email", name="uq_event_attendee"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(
        ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True
    )
    attendee_name: Mapped[str] = mapped_column(String(200), nullable=False)
    attendee_email: Mapped[str] = mapped_column(String(320), nullable=False)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    event: Mapped[Event] = relationship(back_populates="registrations")
