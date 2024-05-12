from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel
from models import User, SessionLocal, Events, Bookings
from typing import Optional
from typing import List
import ast
import uvicorn
import os

app = FastAPI()

# Configure CORS
origins = [
    "http://localhost:3000",  # Your frontend application
    # Add more origins if needed
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



class SignupRequest(BaseModel):
    firstname: str
    lastname: str
    email: str
    username: str
    password: str
    profile_image: Optional[str] = None


class LoginRequest(BaseModel):
    email: str
    password: str


class BookingRequest(BaseModel):
    event_id: int
    user_id: int
    ticket_number: int
    booking_details: Optional[str] = None


class ChangePasswordRequest(BaseModel):
    email: str
    old_password: str
    new_password: str


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/login")
def login(request: LoginRequest, db: Session = Depends(get_db)):
    # Search for the user in the database
    user = db.query(User).filter(User.email == request.email).first()

    if not user or user.password != request.password:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    return user


@app.post("/signup")
def signup(request: SignupRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter((User.username == request.username) | (User.email == request.email)).first()
    if user:
        raise HTTPException(status_code=400, detail="Username or email already exists")

    new_user = User(
        firstname=request.firstname,
        lastname=request.lastname,
        email=request.email,
        username=request.username,
        password=request.password,
        profile_image=request.profile_image or "https://img.icons8.com/fluency/48/administrator-male.png"
    )
    db.add(new_user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Username or email already exists")

    return {"message": "Signup successful!"}


@app.get("/userdetails")
def get_user_details(userid: Optional[int] = None, username: Optional[str] = None, email: Optional[str] = None,
                     db: Session = Depends(get_db)):
    query = db.query(User)

    if userid is not None:
        query = query.filter(User.userid == userid)
    if username is not None:
        query = query.filter(User.username == username)
    if email is not None:
        query = query.filter(User.email == email)

    user = query.first()

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "userid": user.userid,
        "firstname": user.firstname,
        "lastname": user.lastname,
        "email": user.email,
        "username": user.username,
        "password": user.password,
        "profile_image": user.profile_image
    }


@app.get("/eventdetails/{event_id}")
def get_event_details(event_id: int, db: Session = Depends(get_db)):
    event = db.query(Events).filter(Events.event_id == event_id).first()

    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")

    return {
        "event_id": event.event_id,
        "event_title": event.event_title,
        "event_date": event.event_date,
        "event_time": event.event_time,
        "event_description": event.event_description,
        "event_image": event.event_image,
        "event_key_items": ast.literal_eval(event.event_key_items) if event.event_key_items else []
    }


@app.get("/usereventdetails/{user_id}")
def get_user_event_details(user_id: int, db: Session = Depends(get_db)):
    # Fetch all bookings for the given user
    bookings = db.query(Bookings).filter(Bookings.user_id == user_id).all()

    # Initialize an empty list to store event details
    event_details = []

    # For each booking, fetch the corresponding event details
    for booking in bookings:
        event = db.query(Events).filter(Events.event_id == booking.event_id).first()
        if event is not None:
            event_detail = {
                "event_id": event.event_id,
                "event_title": event.event_title,
                "event_date": event.event_date,
                "event_time": event.event_time,
                "event_description": event.event_description,
                "event_image": event.event_image,
                "event_key_items": ast.literal_eval(event.event_key_items) if event.event_key_items else []
            }
            event_details.append(event_detail)

    # If no events found for the user, raise an exception
    if not event_details:
        raise HTTPException(status_code=404, detail="No events found for this user")

    return event_details

@app.get("/alleventdetails")
def get_all_event_details(db: Session = Depends(get_db)):
    events = db.query(Events).all()

    return events


@app.post("/booking")
def create_booking(request: BookingRequest, db: Session = Depends(get_db)):

    new_booking = Bookings(
        event_id=request.event_id,
        user_id=request.user_id,
        ticket_number=request.ticket_number,
        booking_details=""
    )
    db.add(new_booking)
    db.commit()
    return {"message": "Booking successful!"}


@app.get("/bookingdetails")
def get_booking_details(event_id: Optional[int] = None, user_id: Optional[int] = None, db: Session = Depends(get_db)):
    query = db.query(Bookings)

    if event_id is not None:
        query = query.filter(Bookings.event_id == event_id)
    if user_id is not None:
        query = query.filter(Bookings.user_id == user_id)

    bookings = query.all()

    if not bookings:
        raise HTTPException(status_code=404, detail="No bookings found")
    for booking in bookings:
        if isinstance(booking.booking_details, str) and booking.booking_details.startswith('{') and booking.booking_details.endswith('}'):
            booking.booking_details = ast.literal_eval(booking.booking_details)
        else:
            booking.booking_details = str(booking.booking_details)

    return bookings


@app.post("/changepassword")
def change_password(request: ChangePasswordRequest, db: Session = Depends(get_db)):
    # Search for the user in the database
    user = db.query(User).filter(User.email == request.email).first()

    if not user or user.password != request.old_password:
        raise HTTPException(status_code=401, detail="Invalid user id or password")

    # Update the user's password
    user.password = request.new_password
    db.commit()

    # Return the user as a dictionary
    return {
        "userid": user.userid,
        "firstname": user.firstname,
        "lastname": user.lastname,
        "email": user.email,
        "username": user.username,
        "password": user.password,
        "profile_image": user.profile_image
    }
#2
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
