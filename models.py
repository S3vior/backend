from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, ForeignKey , Float ,LargeBinary

from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import JSON
import numpy as np


# create the engine
engine = create_engine('sqlite:///savior.db', echo=True)

# create the base object
Base = declarative_base()

# define the Person model
class Person(Base):
    __tablename__ = 'persons'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    age = Column(String)
    gender = Column(String)
    description = Column(String)
    image = Column(String)
    type = Column(String)
    matched = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    face_encoding = relationship("FaceEncoding", uselist=False, back_populates="person")


    # define the relationship with User
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship("User", back_populates="persons")


    unique_person = relationship("UniquePerson", back_populates="person")

    location = relationship("Location", uselist=False, back_populates="person")

    def __repr__(self):
        return f"<Person(id={self.id}, name={self.name}, age={self.age}, gender={self.gender}, type={self.type}, matched={self.matched})>"


# define the UniquePerson model
class UniquePerson(Base):
    __tablename__ = 'unique_persons'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    age = Column(Integer)
    gender = Column(String)
    description = Column(String)
    type = Column(String)
    created_at = Column(DateTime, default=datetime.now)
    person_id = Column(Integer, ForeignKey('persons.id'))
    person = relationship("Person", back_populates="unique_person")

    def __repr__(self):
        return f"<UniquePerson(id={self.id}, name={self.name}, age={self.age}, gender={self.gender}, type={self.type}, person_id={self.person_id})>"


# define the User model
class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    user_name = Column(String)
    phone_number = Column(String)
    password = Column(String)
    fcm_token = Column(String)
    token = Column(String)
    # define the relationship with Person
    persons = relationship("Person", back_populates="user")

    contacts = relationship("Contact", back_populates="user")

    notifications = relationship("Notification", back_populates="user")

    def __repr__(self):
        return f"<User(id={self.id}, user_name={self.user_name}, phone_number={self.phone_number})>"


class Notification(Base):
    __tablename__ = 'notifications'

    id = Column(Integer, primary_key=True)
    title = Column(String)
    message = Column(String)
    user_id = Column(Integer, ForeignKey('users.id'))

    # Define the relationship with User
    user = relationship("User", back_populates="notifications")

    def __repr__(self):
        return f"<Notification(id={self.id}, message={self.message})>"


class Contact(Base):
    __tablename__ = 'contact_us'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    email = Column(String)
    problem = Column(String)

    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship("User", back_populates="contacts")


    def __repr__(self):
        return f'<Contact {self.id}>'



class FaceEncoding(Base):
    __tablename__ = 'face_encodings'

    id = Column(Integer, primary_key=True)
    person_id = Column(Integer, ForeignKey('persons.id'))
    encoding = Column(LargeBinary)

    person = relationship("Person", back_populates="face_encoding")

    def set_encoding(self, encoding):
        self.encoding = np.array(encoding).tobytes()

    def get_encoding(self):
        return np.frombuffer(self.encoding)

    def __repr__(self):
        return f"<FaceEncoding(person_id={self.person_id})>"

class Match(Base):
    __tablename__ = 'matches'
    id = Column(Integer, primary_key=True)
    match_percentage = Column(String)
    missed_person_id = Column(Integer, ForeignKey('persons.id'))
    found_person_id = Column(Integer, ForeignKey('persons.id'))
    missed_person = relationship("Person", foreign_keys=[missed_person_id])
    found_person = relationship("Person", foreign_keys=[found_person_id])
    # def __repr__(self):
    #     return f"Match(id={self.id}, missed_person={self.missed_person}, found_person={self.found_person})"

class Location(Base):
    __tablename__ = 'locations'

    id = Column(Integer, primary_key=True)
    latitude = Column(Float)
    longitude = Column(Float)
    address = Column(String)
    person_id = Column(Integer, ForeignKey('persons.id'))
    person = relationship("Person", back_populates="location")

    def __repr__(self):
        return f"<Location(id={self.id}, latitude={self.latitude}, longitude={self.longitude})>"


class Source(Base):
    __tablename__ = 'source'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    url = Column(String(200), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    pages = relationship('SourcePage', backref='source', lazy=True)

    scraped_persons = relationship('ScrapedPerson', backref='source', lazy=True)

    def __init__(self, name, url):
        self.name = name
        self.url = url


class SourcePage(Base):
    __tablename__ = 'source_page'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    url = Column(String(200), nullable=False)
    selectors = Column(String, nullable=False)
    scraped = Column(Boolean, default=False)
    type = Column(String,nullable=False)
    max_page_numbers = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    source_id = Column(Integer, ForeignKey('source.id'), nullable=False)

    def __init__(self, name, url, selectors ,type, source, max_page_numbers=None, scraped=False):
        self.name = name
        self.url = url
        self.selectors = selectors
        self.source = source
        self.type = type
        self.max_page_numbers = max_page_numbers
        self.scraped = scraped

class ScrapedPerson(Base):
    __tablename__ = 'scraped_person'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    image = Column(String(200), nullable=False)
    date = Column(String, nullable=True)
    type = Column(String(50), nullable=True)
    source_id = Column(Integer, ForeignKey('source.id'), nullable=False)

    def __init__(self, name, image, date, type, source):
        self.name = name
        self.image = image
        self.date = date
        self.type = type
        self.source = source


# # create the tables
Base.metadata.create_all(engine)
