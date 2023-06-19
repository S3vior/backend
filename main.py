from flask import Flask, jsonify, request, render_template

import face_recognition
import json
import cloudinary
import cloudinary.uploader
import cloudinary.api
from PIL import Image
import urllib.request
import numpy as np


from apscheduler.schedulers.background import BackgroundScheduler

from sqlalchemy.orm import sessionmaker,contains_eager
from sqlalchemy.exc import IntegrityError
from sqlalchemy import create_engine ,func,desc,or_


from models import Person,Match,Contact,User,FaceEncoding ,Location ,Notification
from threading import Thread

from flask_jwt_extended import (
    JWTManager, jwt_required,
    get_jwt_identity
)
from auth import auth_app
from scraping import scrap_app
# from background_job import job_app
from geopy.geocoders import Nominatim
import firebase_admin
from firebase_admin import credentials
from firebase_admin import messaging

app = Flask(__name__)


scheduler = BackgroundScheduler()
app.register_blueprint(auth_app)
app.register_blueprint(scrap_app)

# app.register_blueprint(job_app)

jwt = JWTManager(app)

app.config['JWT_SECRET_KEY'] = 'savior-key'  # set the JWT secret key
app.config['JWT_HEADER_NAME'] = 'token'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = False
engine = create_engine('sqlite:///savior.db', echo=True)
Session = sessionmaker(bind=engine)


cred = credentials.Certificate('sav3or-firebase.json')
firebase_admin.initialize_app(cred)

# create a session
session = Session()

cloudinary.config(
    cloud_name="khaledelabady11",
    api_key="772589215762873",
    api_secret="6EtKMojSfmrBn3t2UMH2wrAODCA"
)

def similars():
    session = Session()
    missing_persons = session.query(Person).filter_by(type="missed",matched=False).all()
    finded_persons = session.query(Person).filter_by(type="founded",matched=False).all()
    if not missing_persons and not finded_persons:
       return jsonify(json.dumps("No More Matchings!"))

    for missed in missing_persons:
        response = urllib.request.urlopen(missed.image)
        image = face_recognition.load_image_file(response)
        p1 = face_recognition.face_encodings(image)
        for found in finded_persons:
            response2 = urllib.request.urlopen(found.image)
            image2 = face_recognition.load_image_file(response2)
            p2 = face_recognition.face_encodings(image2)
            if len(p1) > 0:
                match_results = face_recognition.compare_faces([p1[0]], p2[0])
                if match_results[0]:
                    match = Match(missed_person_id=missed.id, found_person_id=found.id)
                    session.add(match)
                    missed.matched = True  # set matched to True for the missed person
                    found.matched = True   # set matched to True for the found person
                    session.commit()
                    session.close()
                    return jsonify(json.dumps("Match Found!"))

    return jsonify(json.dumps("No Matching Yet!"))


def find_similar():
    with app.app_context():
        similars()

# scheduler.add_job(func=find_similar, trigger="interval", minutes=3)
# scheduler.start()

@app.route('/api/matches', methods=['GET'])
def get_matches():
    session = Session()
    matches = session.query(Match).all()
    result = []
    for match in matches:
        missed_person = session.query(Person).filter_by(id=match.missed_person_id).first()
        found_person = session.query(Person).filter_by(id=match.found_person_id).first()
        result.append({
            'id':match.id,
            "perctage":match.match_percentage,
            'missed_person': {
                'id': missed_person.id,
                'name': missed_person.name,
                'age': missed_person.age,
                'gender': missed_person.gender,
                'description': missed_person.description,
                'image': missed_person.image,
                'type': missed_person.type,
                'location': {
                'address':missed_person.location.address,
               'latitude': missed_person.location.latitude,
               'longitude': missed_person.location.longitude,
               },
            "user": missed_person.user.user_name,
             'created_at': missed_person.created_at.isoformat()},

            'found_person': {
                'id': found_person.id,
                'name': found_person.name,
                'age': found_person.age,
                'gender': found_person.gender,
                'description': found_person.description,
                'image': found_person.image,
                'type': found_person.type,
                'location': {
                'address':found_person.location.address,
               'latitude': found_person.location.latitude,
               'longitude': found_person.location.longitude,
               },
        "user": found_person.user.user_name,
        'created_at': found_person.created_at.isoformat()},

        })
    session.close()
    return jsonify(result)



def uploader(file):
    result = cloudinary.uploader.upload(file)
    return result["secure_url"]


# You can change this to any folder on your system
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# --------------------------------------------------------------------------------------------------------------
# ENDPOINTS
# --------------------------------------------------------------------------------------------------------------


@app.route('/missing_person', methods=['GET', 'POST'])
def upload_image():

    # Check if a valid image file was uploaded
    if request.method == 'POST':
        name = request.form.get("name")
        age = request.form.get("age")
        description = request.form.get("description")
        file = request.files["file"]
        image = uploader(file)
        gender = request.form.get("gender")
        person_type = request.form['type']
        user_id = request.form['user_id']
        new_person = Person(name=name, age=age, gender=gender, description=description,
                            image=image, type=person_type, user_id=2)

    # create a session and add the new person to the database
        session = Session()
        session.add(new_person)
        session.commit()

    # close the session
        session.close()

    # return the new person as a JSON response
        return jsonify(new_person.__dict__)
    # If no valid image file was uploaded, show the file upload form:
    return render_template("form.html")


@app.route('/persons', methods=["GET"])
def list_persons():
    persons = session.query(Person).all()
    return render_template("index.html", data=persons)


# --------------------------------------------------------------------------------------------------------------
# API-ENDPOINTS
# --------------------------------------------------------------------------------------------------------------

@app.route('/api/persons', methods=["GET"])
def get_persons():
    persons =session.query(Person).join(Location).order_by(desc(Person.created_at)).limit(100).all()

    # convert persons to JSON
    persons_json = json.dumps([{
        'id': person.id,
        'name': person.name,
        'age': person.age,
        'gender': person.gender,
        'description': person.description,
        'image': person.image,
        'type': person.type,
        'location': {
            'address':person.location.address,
            'latitude': person.location.latitude,
            'longitude': person.location.longitude,
        },
        "user": person.user.user_name,
        'created_at': person.created_at.isoformat()
    }
    for person in persons])

    # return JSON response
    return persons_json


@app.route('/api/missing_persons', methods=["GET"])
def get_missing_persons():
    persons = session.query(Person).filter_by(type="missed")

    # convert persons to JSON
    persons_json = json.dumps([{
        'id': person.id,
        'name': person.name,
        'age': person.age,
        'gender': person.gender,
        'description': person.description,
        'image': person.image,
        'type': person.type,
        'location': {
            'address':person.location.address,
            'latitude': person.location.latitude,
            'longitude': person.location.longitude,
         },
        "user": person.user.user_name,
        'created_at': person.created_at.isoformat()
    } for person in persons])

    # return JSON response
    return persons_json


@app.route('/api/founded_persons', methods=["GET"])
def get_founded_persons():
    persons = session.query(Person).filter_by(type="founded")

    # convert persons to JSON
    persons_json = json.dumps([{
        'id': person.id,
        'name': person.name,
        'age': person.age,
        'gender': person.gender,
        'description': person.description,
        'image': person.image,
        'type': person.type,
        'location': {
            'address':person.location.address,
            'latitude': person.location.latitude,
            'longitude': person.location.longitude,
        },
        "user": person.user.user_name,
        'created_at': person.created_at.isoformat()
        } for person in persons])

    # return JSON response
    return persons_json

@app.route('/api/matches/<int:match_id>', methods=['GET'])
def get_match(match_id):
    session = Session()
    match = session.query(Match).filter_by(id=match_id).first()
    session.close()

    if not match:
        return jsonify({'error': 'Match not found'}), 404

    missed_person = session.query(Person).filter_by(id=match.missed_person_id).first()
    found_person = session.query(Person).filter_by(id=match.found_person_id).first()

    if not missed_person or not found_person:
        return jsonify({'error': 'Related persons not found'}), 404

    result = {
        'id': match.id,
        'missed_person': {
            'id': missed_person.id,
            'name': missed_person.name,
            'age': missed_person.age,
            'gender': missed_person.gender,
            'description': missed_person.description,
            'image': missed_person.image,
            'type': missed_person.type,
            'location': {
                'address': missed_person.location.address,
                'latitude': missed_person.location.latitude,
                'longitude': missed_person.location.longitude,
            },
            'user': missed_person.user.user_name,
            'created_at': missed_person.created_at.isoformat()
        },
        'found_person': {
            'id': found_person.id,
            'name': found_person.name,
            'age': found_person.age,
            'gender': found_person.gender,
            'description': found_person.description,
            'image': found_person.image,
            'type': found_person.type,
            'location': {
                'address': found_person.location.address,
                'latitude': found_person.location.latitude,
                'longitude': found_person.location.longitude,
            },
            'user': found_person.user.user_name,
            'created_at': found_person.created_at.isoformat()
        }
    }

    return jsonify(result)


@app.route('/persons/<int:person_id>', methods=['DELETE'])
def delete_person(person_id):
    # get a session and the person by id
    session = Session()
    person = session.query(Person).filter_by(id=person_id).first()

    if person:
        # delete the person
        session.delete(person)
        session.commit()

        # return success response
        return jsonify({'message': f'Person with id {person_id} deleted successfully'}), 200
    else:
        # return error response if person not found
        return jsonify({'error': f'Person with id {person_id} not found'}), 404

def get_address(latitude, longitude):
    geolocator = Nominatim(user_agent="savior")
    location = geolocator.reverse((latitude, longitude), exactly_one=True)
    if location is not None:
        return location.address
    else:
        return None


@app.route('/api/persons', methods=['POST'])
@jwt_required()
def create_person():
    try:
        # Get the person data from the request body
        person_details = request.form
        name = person_details['name']
        age = person_details['age']
        description = person_details['description']
        gender = person_details['gender']
        person_type = person_details['type']
        latitude = float(person_details['latitude'])
        longitude = float(person_details['longitude'])

        # Check if required fields are present
        if not all([name, age, gender, person_type]):
            return jsonify({'message': 'Please provide all required fields.'}), 400

        # Upload the image to Cloudinary after enhancing it
        image = request.files.get('image')
        if not image:
            return jsonify({'message': 'Please provide an image.'}), 400


        # Upload the enhanced image to Cloudinary
        uploaded_image = cloudinary.uploader.upload(image)

        # Create a Person record with the uploaded image
        user_id = get_jwt_identity()
        new_person = Person(
            name=name,
            age=age,
            gender=gender,
            description=description,
            type=person_type,
            image=uploaded_image['secure_url'],
            user_id=user_id
        )

        # Create a session and add the new person to the database
        session = Session()
        session.add(new_person)
        session.commit()

        # Create a new PersonLocation record and associate it with the newly created Person
        address = get_address(latitude, longitude)
        new_person_location = Location(
            latitude=latitude,
            longitude=longitude,
            address=address,
            person_id=new_person.id
        )
        session.add(new_person_location)
        session.commit()

        # Run the background task in a separate thread
        thread = Thread(target=save_face_encodings, args=(new_person.image, new_person))
        thread.start()

        return jsonify({'message': 'Person created successfully'}), 201

    except Exception as e:
        # Handle any exceptions and return an appropriate response
        return jsonify({'message': 'An error occurred', 'error': str(e)}), 500

@app.route('/api/persons/<int:person_id>/matches', methods=['GET'])
def get_person_matches(person_id):
    # get a session and the person by id
    session = Session()
    person = session.query(Person).filter_by(id=person_id).first()

    if person:
        # get the matches for the person
        matches = session.query(Match).filter_by(missed_person_id=person_id).all()

        # return a list of matched persons
        matched_persons = []
        for match in matches:
            found_person = session.query(Person).filter_by(id=match.found_person_id).first()

            persons_json = {
                 'id': found_person.id,
                 'name': found_person.name,
                 'age': found_person.age,
                 'gender': found_person.gender,
                 'description': found_person.description,
                 'image': found_person.image,
                 'type': found_person.type,
                 'created_at': found_person.created_at.isoformat(),
            }
    return persons_json

@app.route('/api/persons/<int:person_id>', methods=['GET'])
def get_person(person_id):
    # Retrieve the person from the database based on the provided ID
    person = session.query(Person).filter_by(id=person_id).first()

    if person is None:
        # Return a 404 Not Found error if the person does not exist
        return jsonify({'error': 'Person not found'}), 404

    # Return the person's information as a JSON response
    return jsonify({
        'id': person.id,
        'name': person.name,
        'age': person.age,
        'gender': person.gender,
        'description': person.description,
        'image': person.image,
        'type': person.type,
        'location': {
            'address':person.location.address,
            'latitude': person.location.latitude,
            'longitude': person.location.longitude,
        },
        "user": person.user.user_name,
        'created_at': person.created_at
        # Add any other fields you want to include
    })


# def encode_face(image_url,person_id):
#     response = urllib.request.urlopen(image_url)
#     image = face_recognition.load_image_file(response)
#     encoding = face_recognition.face_encodings(image)[0]

#     # Create a new FaceEncoding object and save it to the database
#     face_encoding = FaceEncoding(person_id=person_id, encoding=encoding.tolist())
#     session.add(face_encoding)
#     session.commit()

#     return encoding

@app.route('/api/persons/search', methods=["GET"])
def search_persons():
    name = request.args.get('name')
    if not name:
        return jsonify({'error': 'Please provide a name parameter'}), 400

    session = Session()
    english_name_query = or_(
        func.lower(func.replace(Person.name, 'أ', 'ا')).like(func.lower(f'%{name}%')),
        func.lower(Person.name).like(func.lower(f'%{name}%'))
    )
    arabic_name_query = func.lower(Person.name).like(func.lower(f'%{name}%'))
    persons = session.query(Person).join(Person.location).options(contains_eager(Person.location)).filter(or_(english_name_query, arabic_name_query)).all()
    session.close()

    if not persons:
        return jsonify({'error': 'Person not found'}), 404

    return jsonify([
        {
            'id': person.id,
            'name': person.name,
            'age': person.age,
            'gender': person.gender,
            'description': person.description,
            'image': person.image,
            'type': person.type,
            'location': {
                'address': person.location.address,
                'latitude': person.location.latitude,
                'longitude': person.location.longitude,
            },
            'created_at': person.created_at.isoformat()
        }
        for person in persons
    ])


@app.route('/api/contact_us', methods=['POST'])
@jwt_required()  # Requires authentication with a JWT token
def contact_us():
    current_user_id = get_jwt_identity()  # Get the current user from the token

    # Get the name, email, and problem from the request body
    name = request.json.get('name')
    email = request.json.get('email')
    problem = request.json.get('problem')

    # Create a new Contact object with the user's ID and the provided name, email, and problem
    contact = Contact(
         name=name, email=email, problem=problem,user_id=current_user_id)

    # Add the new Contact object to the database
    session.add(contact)
    session.commit()

    # Return a success message
    return jsonify({'message': 'Your message has been received. We will get back to you shortly.'}), 200

def store_user_notification(user_id, message):
    notification = Notification(user_id=user_id,message=message)
    session.add(notification)
    session.commit()


@app.route('/api/users/<int:user_id>/notifications', methods=['GET'])
def get_user_notifications(user_id):
    # Create a session
    session = Session()

    try:
        # Query the user and their associated notifications
        # user = session.query(User).get(user_id)
        user_notifications = session.query(Notification).all()
        # user_notifications = session.query(Notification).filter(Notification.user_id == user_id).all()


        # Convert notifications to a list of dictionaries
        notification_list = []
        for notification in user_notifications:
            notification_list.append({
            'id': notification.id,
            'message': notification.message
        })

        return jsonify(notification_list)

    except Exception as e:
        # Handle exceptions and return an error response
        error_message = str(e)
        return jsonify(error=error_message), 500

    finally:
        # Close the session
        session.close()

import cv2
import numpy as np

def enhance_image(image_path):
    # Load the image
    image = cv2.imread(image_path)

    # Apply image enhancement algorithms
    enhanced_image = image.copy()
    enhanced_image = denoise_image(enhanced_image)
    enhanced_image = increase_contrast(enhanced_image)

    # Convert the image to RGB format
    enhanced_image = cv2.cvtColor(enhanced_image, cv2.COLOR_BGR2RGB)

    return enhanced_image

def denoise_image(image):
    # Apply denoising algorithm (e.g., Non-local Means Denoising)
    denoised_image = cv2.fastNlMeansDenoisingColored(image, None, 10, 10, 7, 21)
    return denoised_image

def increase_contrast(image):
    # Apply contrast enhancement algorithm (e.g., Adaptive Histogram Equalization)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    lab_planes = cv2.split(lab)
    lab_planes[0] = clahe.apply(lab_planes[0])
    lab = cv2.merge(lab_planes)
    contrast_enhanced_image = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
    return contrast_enhanced_image

def save_face_encodings(person_image, person):
 # Load the image and find all faces in it
    response = urllib.request.urlopen(person_image)
    image = face_recognition.load_image_file(response)
    face_encodings = face_recognition.face_encodings(image)

    if len(face_encodings) == 0:
        return  # Return if no faces are detected

    face_encoding = face_encodings[0]
    person = session.merge(person)  # Detach the person object from its current session

    # Save the face encoding to the database
    face_encoding_model = FaceEncoding(person=person)
    face_encoding_model.set_encoding(face_encoding)
    session.add(face_encoding_model)
    session.commit()

    # Get the user associated with the person
    user = person.user

    # Create a notification object
    notification = Notification(title = "New Person", message="You uploaded a new person successfully", user=user)
    session.add(notification)
    session.commit()

    user_token = session.query(User.fcm_token).filter(User.id == person.user_id).scalar()

    if user_token:
        # Send FCM notification to the user
        message = f"You Uploaded New Person Successfuly"
        send_fcm_notification(user_token, message)

    search_person(face_encoding,person)


def search_person(img_encoding, person):
    # Retrieve all face encodings from the database
    face_encodings = session.query(FaceEncoding).filter(FaceEncoding.person_id != person.id).all()
    if len(face_encodings) == 0:
        return  # Return if no faces are detected

    # Convert face encodings from the database to a list of numpy arrays
    known_encodings = [fe.get_encoding() for fe in face_encodings]

    # Calculate the face distances and find the best match
    face_distances = np.linalg.norm(known_encodings - img_encoding, axis=1)
    best_match_index = np.argmin(face_distances)
    face_match_percentage = round(((1 - face_distances[best_match_index]) * 100), 1)

    # Check if the match percentage is above 45%
    if face_match_percentage > 45.0:
        matched_person_id = face_encodings[best_match_index].person_id
        matched_person = session.query(Person).get(matched_person_id)
        if matched_person.type == person.type:
            return
        match = Match(match_percentage=str(face_match_percentage),
                      missed_person_id=matched_person_id,
                      found_person_id=person.id)
        session.add(match)
        session.commit()

        user_token = session.query(User.fcm_token).filter(User.id == person.user_id).scalar()
        user = session.query(User).filter(User.id == person.user_id)

        if user_token:
            # Send FCM notification to the user
            message = f"A match has been found for your uploaded person."
            store_user_notification( message , user.id)
            send_fcm_notification(user_token, message)
        return
    else :
        return

def send_fcm_notification(token, message):
    # Construct the notification payload
    notification = messaging.Notification(
        title='New Notification',
        body=message
    )

    # Construct the FCM message
    fcm_message = messaging.Message(
        notification=notification,
        token=token
    )

    # Send the FCM message
    response = messaging.send(fcm_message)
    print('FCM notification sent:', response)


if __name__ == "__main__":
    """
    Here you can change debug and port
    Remember that, in order to make this API functional, you must set debug in False
    """
    app.run(host='0.0.0.0', port=8000, debug=False)
