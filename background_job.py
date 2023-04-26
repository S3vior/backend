from flask import Flask, jsonify, request, redirect, render_template,  make_response ,Blueprint

import face_recognition
import json
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from sqlalchemy import create_engine
# import firebase_admin
# from firebase_admin import credentials, messaging


from models import Person ,UniquePerson ,User

from threading import Thread

app = Flask(__name__)

job_app = Blueprint('job', __name__)

engine = create_engine('sqlite:///savior.db', echo=True)
Session = sessionmaker(bind=engine)
# create a session
session = Session()

# Initialize the Firebase app with your project credentials
# cred = credentials.Certificate('/path/to/serviceAccountKey.json')
# firebase_admin.initialize_app(cred)

# Function to send a notification to a user
def send_notification(user_id, message):
    # Get the user's FCM token from the database
    user = User.query.get(user_id)
    token = user.fcm_token

    # Create a message with the notification content
    notification = messaging.Notification(title='New person added', body=message)

    # Send the notification to the user's device
    message = messaging.Message(notification=notification, token=token)
    response = messaging.send(message)

    return response

def background_task(new_person):
    # Load all the saved person images from the database
    saved_persons = session.query(Person).filter_by(id != new_person.id).all()
    saved_person_encodings = [face_recognition.load_image_file(p.image) for p in saved_persons]
    saved_person_encodings = [face_recognition.face_encodings(img)[0] for img in saved_person_encodings]

    # Encode the image of the new person
    new_person_encoding = face_recognition.load_image_file(new_person.image)
    new_person_encoding = face_recognition.face_encodings(new_person_encoding)[0]

    # Compare the new person encoding with saved person encodings
    matches = face_recognition.compare_faces(saved_person_encodings, new_person_encoding)

    # If a match is found, notify the user
    if any(matches):
        matched_person = saved_persons[matches.index(True)]
        message = f"{matched_person.name} has been added again."
        # send_notification(matched_person.user_id, message)
        return jsonify(message)

    # If no match is found, add the new person to the Unique_Person table
    else:
        new_unique_person = UniquePerson(name=new_person.name, age=new_person.age, gender=new_person.gender,
                                         description=new_person.description, image=new_person.image,
                                         type=new_person.type, user_id=new_person.user_id)
        session = Session()
        session.add(new_unique_person)
        session.commit()
        session.close()
