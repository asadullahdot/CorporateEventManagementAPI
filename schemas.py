"""Pydantic schemas used to validate requests and shape responses."""

import datetime as dt
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


def _reject_blank(value: str) -> str:
    """Strip whitespace and reject strings that are empty afterwards."""
    value = value.strip()
    if not value:
        raise ValueError("must not be empty or whitespace only")
    return value


class EventBase(BaseModel):
    """Fields shared by the event create schema."""

    title: str = Field(..., min_length=1, max_length=200, description="Event title")
    description: Optional[str] = Field(None, description="Optional event description")
    date: dt.date = Field(..., description="Event date (YYYY-MM-DD)")
    location: str = Field(..., min_length=1, max_length=200, description="Event location")
    max_capacity: int = Field(..., gt=0, description="Maximum number of attendees (> 0)")

    _clean_title = field_validator("title")(_reject_blank)
    _clean_location = field_validator("location")(_reject_blank)


class EventCreate(EventBase):
    """Payload for creating an event."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "Python Workshop",
                "description": "Hands-on introduction to FastAPI",
                "date": "2026-11-20",
                "location": "Conference Room A",
                "max_capacity": 30,
            }
        }
    )


class EventUpdate(EventBase):
    """Payload for fully replacing an event (PUT)."""

    model_config = EventCreate.model_config


class EventResponse(BaseModel):
    """Event as returned by the API (no input constraints, so legacy rows still serialise)."""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "title": "Python Workshop",
                "description": "Hands-on introduction to FastAPI",
                "date": "2026-11-20",
                "location": "Conference Room A",
                "max_capacity": 30,
            }
        },
    )

    id: int
    title: str
    description: Optional[str] = None
    date: dt.date
    location: str
    max_capacity: int


class RegistrationCreate(BaseModel):
    """Payload for registering an attendee for an event."""

    attendee_name: str = Field(..., min_length=1, max_length=200, description="Employee name")
    attendee_email: EmailStr = Field(..., description="Employee email (unique per event)")

    _clean_name = field_validator("attendee_name")(_reject_blank)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"attendee_name": "Ayesha Khan", "attendee_email": "ayesha.khan@acme.com"}
        }
    )


class RegistrationResponse(BaseModel):
    """Registration as returned by the API."""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "event_id": 1,
                "attendee_name": "Ayesha Khan",
                "attendee_email": "ayesha.khan@acme.com",
                "created_at": "2026-11-18T09:30:00Z",
            }
        },
    )

    id: int
    event_id: int
    attendee_name: str
    attendee_email: EmailStr
    created_at: dt.datetime
