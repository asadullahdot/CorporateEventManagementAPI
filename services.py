"""Business logic and database operations.

Routes in ``main.py`` call these functions only; all rules (existence checks,
duplicate and capacity limits) live here.
"""

from typing import List

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

import models
import schemas


class NotFoundError(Exception):
    """Raised when a requested event or registration does not exist (HTTP 404)."""


class ConflictError(Exception):
    """Raised when a request violates a business rule (HTTP 409)."""


# --------------------------------------------------------------------------- #
# Events
# --------------------------------------------------------------------------- #
def create_event(db: Session, data: schemas.EventCreate) -> models.Event:
    """Create and persist a new event."""
    event = models.Event(**data.model_dump())
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def list_events(db: Session) -> List[models.Event]:
    """Return all events ordered by date, then id."""
    return list(db.scalars(select(models.Event).order_by(models.Event.date, models.Event.id)))


def get_event(db: Session, event_id: int, lock: bool = False) -> models.Event:
    """Return one event or raise ``NotFoundError``.

    With ``lock=True`` the row is locked (``SELECT ... FOR UPDATE``) until the
    transaction ends, serialising capacity-sensitive operations on the event.
    """
    stmt = select(models.Event).where(models.Event.id == event_id)
    if lock:
        stmt = stmt.with_for_update()
    event = db.scalar(stmt)
    if event is None:
        raise NotFoundError(f"Event with id {event_id} not found")
    return event


def update_event(db: Session, event_id: int, data: schemas.EventUpdate) -> models.Event:
    """Replace an event's fields; raise ``NotFoundError`` if it does not exist."""
    event = get_event(db, event_id, lock=True)
    registered = _count_registrations(db, event_id)
    if data.max_capacity < registered:
        raise ConflictError(
            f"Cannot set capacity to {data.max_capacity}: {registered} attendees already registered"
        )
    for field, value in data.model_dump().items():
        setattr(event, field, value)
    db.commit()
    db.refresh(event)
    return event


def delete_event(db: Session, event_id: int) -> None:
    """Delete an event (and its registrations); raise ``NotFoundError`` if missing."""
    event = get_event(db, event_id)
    db.delete(event)
    db.commit()


# --------------------------------------------------------------------------- #
# Registrations
# --------------------------------------------------------------------------- #
def _count_registrations(db: Session, event_id: int) -> int:
    """Return how many registrations an event currently has."""
    return db.scalar(
        select(func.count(models.Registration.id)).where(models.Registration.event_id == event_id)
    ) or 0


def create_registration(
    db: Session, event_id: int, data: schemas.RegistrationCreate
) -> models.Registration:
    """Register an attendee, enforcing existence, duplicate and capacity rules."""
    # Lock the event row so concurrent registrations cannot overbook it.
    event = get_event(db, event_id, lock=True)  # 404 if the event does not exist

    email = data.attendee_email.lower()
    duplicate = db.scalar(
        select(models.Registration.id).where(
            models.Registration.event_id == event_id,
            func.lower(models.Registration.attendee_email) == email,
        )
    )
    if duplicate is not None:
        raise ConflictError(f"{email} is already registered for this event")

    if _count_registrations(db, event_id) >= event.max_capacity:
        raise ConflictError(f"Event is full (capacity {event.max_capacity})")

    registration = models.Registration(
        event_id=event_id, attendee_name=data.attendee_name, attendee_email=email
    )
    db.add(registration)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        # Event deleted meanwhile -> 404; otherwise the unique index caught a duplicate.
        if db.get(models.Event, event_id) is None:
            raise NotFoundError(f"Event with id {event_id} not found") from None
        raise ConflictError(f"{email} is already registered for this event") from None
    db.refresh(registration)
    return registration


def list_registrations(db: Session, event_id: int) -> List[models.Registration]:
    """Return all registrations of an event; ``NotFoundError`` if the event is missing."""
    get_event(db, event_id)
    return list(
        db.scalars(
            select(models.Registration)
            .where(models.Registration.event_id == event_id)
            .order_by(models.Registration.id)
        )
    )


def delete_registration(db: Session, registration_id: int) -> None:
    """Cancel a registration; raise ``NotFoundError`` if it does not exist."""
    registration = db.get(models.Registration, registration_id)
    if registration is None:
        raise NotFoundError(f"Registration with id {registration_id} not found")
    db.delete(registration)
    db.commit()
