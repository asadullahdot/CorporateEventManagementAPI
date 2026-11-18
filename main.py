"""API endpoints and application entry point.

Routes are intentionally thin: they validate input via schemas, delegate to
``services`` and let the exception handlers translate domain errors to HTTP.
"""

from contextlib import asynccontextmanager
from typing import List

from fastapi import Depends, FastAPI, Request, status
from fastapi.responses import JSONResponse, Response
from sqlalchemy.orm import Session

import models
import schemas
import services
from db import Base, engine, get_db


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Create database tables on startup."""
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Corporate Event Management API",
    description="Manage Acme Corp events and employee registrations.",
    version="1.0.0",
    lifespan=lifespan,
    openapi_tags=[
        {"name": "Events", "description": "Create, read, update and delete events."},
        {"name": "Registrations", "description": "Register attendees for events."},
    ],
)

ERR_404 = {404: {"description": "Resource not found"}}
ERR_409 = {409: {"description": "Business rule conflict"}}


@app.exception_handler(services.NotFoundError)
async def not_found_handler(_: Request, exc: services.NotFoundError) -> JSONResponse:
    """Map ``NotFoundError`` to a 404 response."""
    return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"detail": str(exc)})


@app.exception_handler(services.ConflictError)
async def conflict_handler(_: Request, exc: services.ConflictError) -> JSONResponse:
    """Map ``ConflictError`` to a 409 response."""
    return JSONResponse(status_code=status.HTTP_409_CONFLICT, content={"detail": str(exc)})


# ------------------------------- Events ------------------------------------ #
@app.post(
    "/events",
    response_model=schemas.EventResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Events"],
    summary="Create an event",
)
def create_event(data: schemas.EventCreate, db: Session = Depends(get_db)) -> models.Event:
    """Create a new event."""
    return services.create_event(db, data)


@app.get("/events", response_model=List[schemas.EventResponse], tags=["Events"], summary="List events")
def list_events(db: Session = Depends(get_db)) -> List[models.Event]:
    """Return all events."""
    return services.list_events(db)


@app.get(
    "/events/{event_id}",
    response_model=schemas.EventResponse,
    responses=ERR_404,
    tags=["Events"],
    summary="Get one event",
)
def get_event(event_id: int, db: Session = Depends(get_db)) -> models.Event:
    """Return a single event by id."""
    return services.get_event(db, event_id)


@app.put(
    "/events/{event_id}",
    response_model=schemas.EventResponse,
    responses={**ERR_404, **ERR_409},
    tags=["Events"],
    summary="Update an event",
)
def update_event(
    event_id: int, data: schemas.EventUpdate, db: Session = Depends(get_db)
) -> models.Event:
    """Replace an event's details."""
    return services.update_event(db, event_id, data)


@app.delete(
    "/events/{event_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=ERR_404,
    tags=["Events"],
    summary="Delete an event",
)
def delete_event(event_id: int, db: Session = Depends(get_db)) -> Response:
    """Delete an event and all of its registrations."""
    services.delete_event(db, event_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------------------------- Registrations -------------------------------- #
@app.post(
    "/events/{event_id}/registrations",
    response_model=schemas.RegistrationResponse,
    status_code=status.HTTP_201_CREATED,
    responses={**ERR_404, **ERR_409},
    tags=["Registrations"],
    summary="Register for an event",
)
def create_registration(
    event_id: int, data: schemas.RegistrationCreate, db: Session = Depends(get_db)
) -> models.Registration:
    """Register an attendee. 404 if no such event; 409 if duplicate or event is full."""
    return services.create_registration(db, event_id, data)


@app.get(
    "/events/{event_id}/registrations",
    response_model=List[schemas.RegistrationResponse],
    responses=ERR_404,
    tags=["Registrations"],
    summary="List registrations for an event",
)
def list_registrations(event_id: int, db: Session = Depends(get_db)) -> List[models.Registration]:
    """Return all registrations of an event."""
    return services.list_registrations(db, event_id)


@app.delete(
    "/registrations/{registration_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=ERR_404,
    tags=["Registrations"],
    summary="Cancel a registration",
)
def delete_registration(registration_id: int, db: Session = Depends(get_db)) -> Response:
    """Cancel a registration by id."""
    services.delete_registration(db, registration_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
