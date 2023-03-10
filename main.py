"""
    API REST con Python 3 y SQLite 3
"""
from flask import Flask, jsonify, request, redirect, render_template,  make_response

import face_recognition
import json
import cloudinary
from cloudinary.uploader import upload
from cloudinary.utils import cloudinary_url
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


from models import Person
from models import User

from flask_jwt_extended import (
    JWTManager, jwt_required, create_access_token,
    get_jwt_identity
)
from auth import auth_app
app = Flask(__name__)

app.register_blueprint(auth_app)

app.config['JWT_SECRET_KEY'] = 'savior-key'  # set the JWT secret key
jwt = JWTManager(app)

engine = create_engine('sqlite:///missing_persons.db', echo=True)
Session = sessionmaker(bind=engine)

# create a session
session = Session()


def print_date_time():
    print(time.strftime("%A, %d. %B %Y %I:%M:%S %p"))


scheduler = BackgroundScheduler()
# # Create the job
# scheduler.add_job(func=print_date_time, trigger="interval", seconds=30)
# # Start the scheduler
# scheduler.start()

cloudinary.config(
    cloud_name="khaledelabady11",
    api_key="772589215762873",
    api_secret="6EtKMojSfmrBn3t2UMH2wrAODCA"
)


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


def detect_faces_in_image(person_id):
    person = missing_person_controller.get_by_id(person_id)
    response = urllib.request.urlopen(person[5])
    image = face_recognition.load_image_file(response)
    face_encodings = face_recognition.face_encodings(image)[0]
    json_data = json.dumps(face_encodings.tolist())
    result = faces_controller.insert_face(person_id, json_data)
    return jsonify(result)


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
                            image=image, type=person_type, user_id=user_id)

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


@app.route("/api/persons", methods=["POST"])
@jwt_required
def insert_person():
    person_details = request.get_json()
    name = person_details("name")
    age = person_details("age")
    description = person_details("description")
    file = request.files["file"]
    image = uploader(file)
    gender = person_details("gender")
    person_type = person_details['type']
    user_id = get_jwt_identity()
    new_person = Person(name=name, age=age, gender=gender, description=description,
                        image=image, type=person_type, user_id=user_id)

    # create a session and add the new person to the database
    session = Session()
    session.add(new_person)
    session.commit()

    # close the session
    session.close()

    # return the new person as a JSON response
    return jsonify(new_person.__dict__)


# @app.route("/api/missing_persons/<id>", methods=["PUT"])
# def update_person(id):
#     person_details = request.get_json()
#     name = person_details["name"]
#     message = person_details["message"]
#     result = missing_person_controller.update_person(id, name, message)
#     return jsonify(result)


# @app.route("/api/persons/<id>", methods=["DELETE"])
# def delete_person(id):
#     result = missing_person_controller.delete_person(id)
#     return jsonify(result)


# @app.route("/api/missing_persons/<id>", methods=["GET"])
# def get_person_by_id(id):
#     person = missing_person_controller.get_by_id(id)
#     json_str = {
#         "id": person[0],
#         "name": person[1],
#         "age": person[2],
#         "description": person[3],
#         "gender": person[4],
#         "image": person[5],
#         "created_at": person[6]
#     }
#     return jsonify(json_str)


# @app.route("/api/found_person/<id>", methods=["DELETE"])
# def delete_founded_person(id):
#     found_persons_controller.delete_person(id)
#     return "true"


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
def find_similar(id):
    persons = persons = session.query(Person).filter_by(type="founded")
    person = session.query(Person).filter_by(id=id)
    response = urllib.request.urlopen(person[4])
    image = face_recognition.load_image_file(response)
    p1 = face_recognition.face_encodings(image)
    for x in persons:
        response2 = urllib.request.urlopen(x[5])
        image2 = face_recognition.load_image_file(response2)
        p2 = face_recognition.face_encodings(image2)
        res = []
        if len(p1) > 0:
            match_results = face_recognition.compare_faces([p1[0]], p2[0])
            if match_results[0] == True:
                res.append({"id": x[0],
                            "name": x[1],
                            "age": x[2],
                            "description": x[3],
                            "gender": x[4],
                            "image": x[5],
                            "created_at": x[6]})
                return jsonify(res)
    return jsonify(json.dumps("not exited yet!"))


@app.route("/api/similars")
def similars():
    missing_persons = found_persons_controller.get_persons()
    finded_persons = missing_person_controller.get_persons()
    # response = urllib.request.urlopen(person[5])
    # image = face_recognition.load_image_file(response)
    # p1= face_recognition.face_encodings(image)
    for missed in missing_persons:
        # if x == person:
        #     continue
        response = urllib.request.urlopen(missed[4])
        image = face_recognition.load_image_file(response)
        p1 = face_recognition.face_encodings(image)
        for found in finded_persons:
            response2 = urllib.request.urlopen(found[5])
            image2 = face_recognition.load_image_file(response2)
            p2 = face_recognition.face_encodings(image2)
            if len(p1) > 0:

                match_results = face_recognition.compare_faces([p1[0]], p2[0])
                if match_results[0] == True:
                 #   str = "May be the person with id = {}"
                    found[8] = missed[0]
                    return jsonify(found[0])

    return jsonify(json.dumps("not exited"))


if __name__ == "__main__":
    """
    Here you can change debug and port
    Remember that, in order to make this API functional, you must set debug in False
    """
    app.run(host='0.0.0.0', port=8000, debug=False)
