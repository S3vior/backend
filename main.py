"""
    API REST con Python 3 y SQLite 3
"""
from flask import Flask, jsonify, request, redirect ,render_template
import person_controller
import face_recognition
from db import create_tables
import json
import cloudinary
from cloudinary.uploader import upload
from cloudinary.utils import cloudinary_url
from PIL import Image
import urllib.request

app = Flask(__name__)

cloudinary.config(
  cloud_name = "khaledelabady11",
  api_key = "772589215762873",
  api_secret = "6EtKMojSfmrBn3t2UMH2wrAODCA"
)

def uploader(file):
    result = cloudinary.uploader.upload(file)
    return result["secure_url"]

# You can change this to any folder on your system
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS



@app.route('/person', methods=['GET', 'POST'])
def upload_image():

    # Check if a valid image file was uploaded
    if request.method == 'POST':
        name = request.form.get("name")
        message = request.form.get("message")
        age = request.form.get("age")
        description = request.form.get("description")
        file =request.files["file"]
        # face_encodings=detect_faces_in_image(file)
        image= uploader(file)
        result = person_controller.insert_person(name,age,message,description,image)
        return jsonify(result)


    # If no valid image file was uploaded, show the file upload form:
    return render_template("form.html")
@app.route("/")
def detect_faces_in_image():
    person = person_controller.get_by_id(1)
    response = urllib.request.urlopen(person[5])
    image = face_recognition.load_image_file(response)
    face_encodings = face_recognition.face_encodings(image)[0]
    json_data= json.dumps(face_encodings.tolist())
    result = person_controller.insert_face(1,json_data)
    return jsonify(result)

@app.route('/api/persons', methods=["GET"])
def get_games():
    persons = person_controller.get_persons()
    person_list = []
    for person in persons:
        person_list.append(
            {
                "id": person[0],
                "name": person[1],
                "age": person[2],
                "description": person[3],
                "message": person[4],
                "image": person[5]

                # "created_on": person["created_on"],
            }
        )
    return jsonify(person_list)

# @app.route("/person", methods=["POST"])
# def add_person():
#     name = request.files['name']
#     message = request.files['message']
#     result = game_controller.insert_game(name, message)
#     return jsonify(result)

@app.route("/api/persons", methods=["POST"])
def insert_person():
    person_details = request.get_json()
    name = person_details["name"]
    file = person_details["image"]
    # image_encoding=detect_faces_in_image(file)
    image = uploader(file)
    message = person_details["message"]
    age = person_details["age"]
    description = person_details["description"]

    result = person_controller.insert_person(name,age,description, message,image)
    return jsonify(result)


@app.route("/api/persons/<id>", methods=["PUT"])
def update_person(id):
    person_details = request.get_json()
    name = person_details["name"]
    message = person_details["message"]
    result = person_controller.update_person(id,name, message)
    return jsonify(result)


@app.route("/api/persons/<id>", methods=["DELETE"])
def delete_person(id):
    result = person_controller.delete_person(id)
    return jsonify(result)


@app.route("/api/persons/<id>", methods=["GET"])
def get_person_by_id(id):
    person = person_controller.get_by_id(id)
    json_str= {
                "id": person[0],
                "name": person[1],
                "age": person[2],
                "description": person[3],
                "message": person[4],
                "image": person[5]

                # "created_on": person["created_on"],
            }
    return jsonify(json_str)


#get Face_encodings
@app.route('/api/faces', methods=["GET"])
def get_faces():
    faces = person_controller.get_faces()
    face_list = []
    for face in faces:
        face_list.append(
            {
                "person_id": face[0],
                "data": face[1],
                # "created_on": person["created_on"],
            }
        )
    return jsonify(face_list)

if __name__ == "__main__":
    create_tables()
    """
    Here you can change debug and port
    Remember that, in order to make this API functional, you must set debug in False
    """
    app.run(host='0.0.0.0', port=8000, debug=False)
