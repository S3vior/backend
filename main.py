"""
    API REST con Python 3 y SQLite 3
"""
from flask import Flask, jsonify, request, redirect, render_template,  make_response

import face_recognition
import json
import cloudinary
import cloudinary.uploader
import cloudinary.api
from PIL import Image
import urllib.request
import ast
import numpy as np

import time
import atexit

from apscheduler.schedulers.background import BackgroundScheduler

import requests
from bs4 import BeautifulSoup

from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from sqlalchemy import create_engine


from models import Person , Match
from models import User
from models import FaceEncoding
from threading import Thread
from datetime import timedelta

from flask_jwt_extended import (
    JWTManager, jwt_required,
    get_jwt_identity
)
from auth import auth_app
from background_job import job_app

app = Flask(__name__)

app.register_blueprint(auth_app)
app.register_blueprint(job_app)


app.config['JWT_SECRET_KEY'] = 'savior-key'  # set the JWT secret key
app.config['JWT_HEADER_NAME'] = 'token'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=5)


jwt = JWTManager(app)

engine = create_engine('sqlite:///savior.db', echo=True)
Session = sessionmaker(bind=engine)

# create a session
session = Session()

cloudinary.config(
    cloud_name="khaledelabady11",
    api_key="772589215762873",
    api_secret="6EtKMojSfmrBn3t2UMH2wrAODCA"
)

# @app.route("/api/similars")
def similars():
    session = Session()
    missing_persons = session.query(Person).filter_by(type="missed").all()
    finded_persons = session.query(Person).filter_by(type="founded").all()


    for missed in missing_persons:
        # if x == person:
        #     continue
        response = urllib.request.urlopen(missed.image)
        image = face_recognition.load_image_file(response)
        p1 = face_recognition.face_encodings(image)
        for found in finded_persons:
            response2 = urllib.request.urlopen(found.image)
            image2 = face_recognition.load_image_file(response2)
            p2 = face_recognition.face_encodings(image2)
            if len(p1) > 0:

                match_results = face_recognition.compare_faces([p1[0]], p2[0])
                if match_results[0] == True:
                    match = Match( missed_person_id=missed.id, found_person_id=found.id)
                    session = Session()
                    session.add(match)
                    session.commit()
                    session.close()

    return jsonify(json.dumps("No Matching Yet!"))

# scheduler = BackgroundScheduler()
# # Create the job
# scheduler.add_job(func=similars, trigger="interval", seconds=30)
# # Start the scheduler
# scheduler.start()


@app.route('/matches', methods=['GET'])
def get_matches():
    session = Session()
    matches = session.query(Match).all()
    result = []
    for match in matches:
        missed_person = session.query(Person).filter_by(id=match.missed_person_id).first()
        found_person = session.query(Person).filter_by(id=match.found_person_id).first()
        result.append({
            'missed_person': {
                'id': missed_person.id,
                'name': missed_person.name,
                'age': missed_person.age,
                'gender': missed_person.gender,
                'description': missed_person.description,
                'image': missed_person.image,
                'type': missed_person.type
            },
            'found_person': {
                'id': found_person.id,
                'name': found_person.name,
                'age': found_person.age,
                'gender': found_person.gender,
                'description': found_person.description,
                'image': found_person.image,
                'type': found_person.type
            }
        })
    session.close()
    return jsonify(result)




def uploader(file):
    result = cloudinary.uploader.upload(file)
    return result["secure_url"]


# You can change this to any folder on your system
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}


@app.route('/scraper')
def scrap_img():
    htmldata = requests.get('https://atfalmafkoda.com/ar/home').text
    soup = BeautifulSoup(htmldata, 'html.parser')
    images = soup.find_all('div', class_='slid_img')
    res = []
    for item in images:
        res.append({"name": (item.h1.text),
                    "image": ("https://atfalmafkoda.com"+item.img["src"]),
                    "date": (item.p.text)})
    return jsonify(res)



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
    persons = session.query(Person).all()

    # convert persons to JSON
    persons_json = json.dumps([{
        'id': person.id,
        'name': person.name,
        'age': person.age,
        'gender': person.gender,
        'description': person.description,
        'image': person.image,
        'type': person.type,
        'created_at': person.created_at.isoformat(),
    } for person in persons])

    # return JSON response
    return persons_json


@app.route('/api/missing_persons', methods=["GET"])
def get_missing_persons():
    persons = session.query(Person).filter_by(type="missing")

    # convert persons to JSON
    persons_json = json.dumps([{
        'id': person.id,
        'name': person.name,
        'age': person.age,
        'gender': person.gender,
        'description': person.description,
        'image': person.image,
        'type': person.type,
        'created_at': person.created_at.isoformat(),
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
        'created_at': person.created_at.isoformat(),
    } for person in persons])

    # return JSON response
    return persons_json

@app.route('/api/users', methods=["GET"])
def get_users():
    users = session.query(User).all()

    # convert persons to JSON
    users_json = json.dumps([{
        'id': user.id,
        'name': user.user_name,
        # 'token': user.get_access_token(identity=user.id),
    } for user in users])

    # return JSON response
    return users_json
@app.route('/api/persons', methods=['POST'])
@jwt_required()
def create_person():
    # get the person data from the request body
    person_details = request.form
    name = person_details['name']
    age = person_details['age']
    description = person_details['description']
    gender = person_details['gender']
    person_type = person_details['type']

    # check if required fields are present
    if not all([name, age, gender, person_type]):
        return jsonify({'message': 'Please provide all required fields.'}), 400

    # upload the image to Cloudinary
    image = request.files['image']
    if not image:
        return jsonify({'message': 'Please provide an image.'}), 400

    uploaded_image = cloudinary.uploader.upload(image)
    # create a Person record with the uploaded image
    user_id = get_jwt_identity()
    new_person = Person(name=name, age=age, gender=gender, description=description,
                        type=person_type, image=uploaded_image["secure_url"], user_id=user_id)

    # create a session and add the new person to the database
    session = Session()
    session.add(new_person)
    session.commit()
#      encode_face(new_person.image ,new_person.id)

#       # Run the background task in a separate thread
#     # thread = Thread(target=job_app, args=(new_person,))
#     # thread.start()

    return jsonify({'message': 'Person created successfully'}), 201




# get Face_encodings
# @app.route('/api/faces', methods=["GET"])
# def get_faces():
#     faces = faces_controller.get_faces()
#     face_list = []
#     for face in faces:
#         face_list.append(
#             {
#                 "person_id": face[0],
#                 "data": face[1],
#                 # "created_on": person["created_on"],
#             }
#         )
#     return jsonify(face_list)

@app.route("/api/missing_persons/<id>/similar")
def search_for_face(id):
    person = session.query(Person).filter_by(id=id).first()

    # Load the target image
    response = urllib.request.urlopen(person.image)
    target_image = face_recognition.load_image_file(response)

    # Encode the target face
    target_encodings = face_recognition.face_encodings(target_image)

    # Check if there are any faces in the target image
    if len(target_encodings) == 0:
        return jsonify([])

    # Query the database for all known faces
    known_persons = session.query(Person).filter_by(type="founded").all()

    # Encode all the known faces
    known_encodings = [face_recognition.face_encodings(face_recognition.load_image_file(urllib.request.urlopen(person.image)))[0] for person in known_persons]

    # Compare the target face to all the known faces
    matches = face_recognition.compare_faces(known_encodings, target_encodings[0])

    # Find the indices of all the matching faces
    matching_indices = [i for i, match in enumerate(matches) if match]

    # Get the ids of all the matching persons
    matching_ids = [known_persons[i].id for i in matching_indices]
    matching_ids.remove(person.id)

    return jsonify(matching_ids)

def encode_face(image_url,person_id):
    response = urllib.request.urlopen(image_url)
    image = face_recognition.load_image_file(response)
    encoding = face_recognition.face_encodings(image)[0]

    # Create a new FaceEncoding object and save it to the database
    face_encoding = FaceEncoding(person_id=person_id, encoding=encoding.tolist())
    session.add(face_encoding)
    session.commit()

    return encoding


@app.route('/api/persons/search',methods=["GET"])
def search_persons():
    name = request.args.get('name')
    if not name:
        return jsonify({'error': 'Please provide a name parameter'}), 400

    session = Session()
    persons = session.query(Person).filter_by(name=name).all()
    if not persons:
        return jsonify({'error': 'Person not found'}), 404
    session.close()
    results = []
    for person in persons:
        results.append({
            'id': person.id,
            'name': person.name,
            'age': person.age,
            'gender': person.gender
        })
    return jsonify(results)




if __name__ == "__main__":
    """
    Here you can change debug and port
    Remember that, in order to make this API functional, you must set debug in False
    """
    app.run(host='0.0.0.0', port=8000, debug=False)
