"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import os
from pathlib import Path
from typing import List, Optional
from datetime import datetime

# Persistence
from sqlmodel import SQLModel, Field, create_engine, Session, select

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

# In-memory activity database
activities = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"]
    },
    "Soccer Team": {
        "description": "Join the school soccer team and compete in matches",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 22,
        "participants": ["liam@mergington.edu", "noah@mergington.edu"]
    },
    "Basketball Team": {
        "description": "Practice and play basketball with the school team",
        "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["ava@mergington.edu", "mia@mergington.edu"]
    },
    "Art Club": {
        "description": "Explore your creativity through painting and drawing",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["amelia@mergington.edu", "harper@mergington.edu"]
    },
    "Drama Club": {
        "description": "Act, direct, and produce plays and performances",
        "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 20,
        "participants": ["ella@mergington.edu", "scarlett@mergington.edu"]
    },
    "Math Club": {
        "description": "Solve challenging problems and participate in math competitions",
        "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
        "max_participants": 10,
        "participants": ["james@mergington.edu", "benjamin@mergington.edu"]
    },
    "Debate Team": {
        "description": "Develop public speaking and argumentation skills",
        "schedule": "Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 12,
        "participants": ["charlotte@mergington.edu", "henry@mergington.edu"]
    }
}


# --- New: SQLite-backed Event and News models (minimal MVP) ---
DATABASE_URL = "sqlite:///./mergington.db"
engine = create_engine(DATABASE_URL, echo=False)


class Event(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    description: Optional[str] = None
    location: Optional[str] = None
    start_datetime: Optional[datetime] = None
    end_datetime: Optional[datetime] = None
    capacity: Optional[int] = None
    # attendees stored as comma-separated emails for MVP
    attendees: Optional[str] = None
    organizer: Optional[str] = None
    tags: Optional[str] = None


class News(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    body: Optional[str] = None
    author: Optional[str] = None
    published_at: Optional[datetime] = None
    tags: Optional[str] = None


def init_db():
    SQLModel.metadata.create_all(engine)


# initialize DB on import/start
init_db()


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    return activities


# --- Event endpoints ---
@app.get("/events")
def list_events():
    with Session(engine) as session:
        events = session.exec(select(Event)).all()
        return events


@app.post("/events")
def create_event(event: Event):
    with Session(engine) as session:
        session.add(event)
        session.commit()
        session.refresh(event)
        return event


@app.get("/events/{event_id}")
def get_event(event_id: int):
    with Session(engine) as session:
        event = session.get(Event, event_id)
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        return event


@app.put("/events/{event_id}")
def update_event(event_id: int, payload: Event):
    with Session(engine) as session:
        event = session.get(Event, event_id)
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        for k, v in payload.dict(exclude_unset=True).items():
            setattr(event, k, v)
        session.add(event)
        session.commit()
        session.refresh(event)
        return event


@app.delete("/events/{event_id}")
def delete_event(event_id: int):
    with Session(engine) as session:
        event = session.get(Event, event_id)
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        session.delete(event)
        session.commit()
        return {"message": "deleted"}


def _parse_attendees(s: Optional[str]) -> List[str]:
    if not s:
        return []
    return [e for e in s.split(",") if e]


def _join_attendees(lst: List[str]) -> str:
    return ",".join(lst)


@app.post("/events/{event_id}/signup")
def signup_event(event_id: int, email: str):
    with Session(engine) as session:
        event = session.get(Event, event_id)
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        attendees = _parse_attendees(event.attendees)
        if email in attendees:
            raise HTTPException(status_code=400, detail="Already signed up")
        if event.capacity and len(attendees) >= event.capacity:
            raise HTTPException(status_code=400, detail="Event is full")
        attendees.append(email)
        event.attendees = _join_attendees(attendees)
        session.add(event)
        session.commit()
        session.refresh(event)
        return {"message": f"Signed up {email}"}


@app.post("/events/{event_id}/unregister")
def unregister_event(event_id: int, email: str):
    with Session(engine) as session:
        event = session.get(Event, event_id)
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        attendees = _parse_attendees(event.attendees)
        if email not in attendees:
            raise HTTPException(status_code=400, detail="Not signed up")
        attendees.remove(email)
        event.attendees = _join_attendees(attendees)
        session.add(event)
        session.commit()
        session.refresh(event)
        return {"message": f"Unregistered {email}"}


@app.post("/events/{event_id}/checkin")
def checkin_event(event_id: int, email: str):
    # For MVP, checkin is the same as ensuring attendee exists; real checkin would add attendance record
    with Session(engine) as session:
        event = session.get(Event, event_id)
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        attendees = _parse_attendees(event.attendees)
        if email not in attendees:
            raise HTTPException(status_code=400, detail="Student not registered")
        return {"message": f"Checked in {email}"}


# --- News endpoints ---
@app.get("/news")
def list_news():
    with Session(engine) as session:
        items = session.exec(select(News)).all()
        return items


@app.post("/news")
def create_news(item: News):
    if not item.published_at:
        item.published_at = datetime.utcnow()
    with Session(engine) as session:
        session.add(item)
        session.commit()
        session.refresh(item)
        return item


@app.get("/news/{news_id}")
def get_news(news_id: int):
    with Session(engine) as session:
        item = session.get(News, news_id)
        if not item:
            raise HTTPException(status_code=404, detail="News not found")
        return item


@app.put("/news/{news_id}")
def update_news(news_id: int, payload: News):
    with Session(engine) as session:
        item = session.get(News, news_id)
        if not item:
            raise HTTPException(status_code=404, detail="News not found")
        for k, v in payload.dict(exclude_unset=True).items():
            setattr(item, k, v)
        session.add(item)
        session.commit()
        session.refresh(item)
        return item


@app.delete("/news/{news_id}")
def delete_news(news_id: int):
    with Session(engine) as session:
        item = session.get(News, news_id)
        if not item:
            raise HTTPException(status_code=404, detail="News not found")
        session.delete(item)
        session.commit()
        return {"message": "deleted"}



@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, email: str):
    """Sign up a student for an activity"""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is not already signed up
    if email in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is already signed up"
        )

    # Add student
    activity["participants"].append(email)
    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(activity_name: str, email: str):
    """Unregister a student from an activity"""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is signed up
    if email not in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is not signed up for this activity"
        )

    # Remove student
    activity["participants"].remove(email)
    return {"message": f"Unregistered {email} from {activity_name}"}
