from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

# create the engine
engine = create_engine('sqlite:///missing_persons.db', echo=True)

# create the base object
Base = declarative_base()

# define the Person model
class Person(Base):
    __tablename__ = 'persons'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    age = Column(Integer)
    gender = Column(String)
    description = Column(String)
    image = Column(String)
    type = Column(String)
    created_at = Column(DateTime, default=datetime.now)

    # define the relationship with User
    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship("User", back_populates="persons")

    def __repr__(self):
        return f"<Person(id={self.id}, name={self.name}, age={self.age}, gender={self.gender}, type={self.type})>"

# define the User model
class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    user_name = Column(String)
    phone_number = Column(String)
    password = Column(String)
    # define the relationship with Person
    persons = relationship("Person", back_populates="user")

    def __repr__(self):
        return f"<User(id={self.id}, user_name={self.user_name}, phone_number={self.phone_number})>"

# create the tables
Base.metadata.create_all(engine)
