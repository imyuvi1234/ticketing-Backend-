from sqlalchemy import Column, Integer, String, create_engine, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import mysql.connector

Base = declarative_base()


class User(Base):
    __tablename__ = 'user'
    userid = Column(Integer, primary_key=True, index=True)
    firstname = Column(String(50))
    lastname = Column(String(50))
    email = Column(String(100), unique=True, index=True)
    username = Column(String(50), unique=True, index=True)
    password = Column(String(100))
    profile_image = Column(String(500), nullable=False,
                           default="https://img.icons8.com/fluency/48/administrator-male.png")


class Events(Base):
    __tablename__ = 'events'
    event_id = Column(Integer, primary_key=True, index=True)
    event_title = Column(String(100))
    event_date = Column(String(10))
    event_time = Column(String(5))
    event_description = Column(String(500))
    event_image = Column(String(500))
    event_key_items = Column(String(500))


class Bookings(Base):
    __tablename__ = 'bookings'
    booking_id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey('events.event_id'))
    user_id = Column(Integer, ForeignKey('user.userid'))
    ticket_number = Column(Integer)
    booking_details = Column(String(500), nullable=False,
                             default={"abc": "xyz"})

  # mysql+pymysql://<db_user>:<db_pass>@<db_host>:<db_port>/<db_name>
DATABASE_URL = "mysql+pymysql://root:root123@35.197.247.203:3306/esrs"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)
