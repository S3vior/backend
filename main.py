"""
    API REST con Python 3 y SQLite 3
"""
from flask import Flask, jsonify, request, redirect ,render_template
import person_controller
import face_recognition
from db import create_tables
import json

app = Flask(__name__)

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
        result = person_controller.insert_game(name, message)
        return jsonify(result)


    # If no valid image file was uploaded, show the file upload form:
    return render_template("form.html")

def detect_faces_in_image(file_stream):

    # mo_image = face_recognition.load_image_file("khaled.jpg")
    # mo_face_encoding = face_recognition.face_encodings(mo_image)[0]

    # # shiba_image = face_recognition.load_image_file("shiba.jpg")
    # # shiba_face_encoding = face_recognition.face_encodings(shiba_image)[0]

    # known_face_encodings = [
    # mo_face_encoding]
    # Load the uploaded image file
    img = face_recognition.load_image_file(file_stream)

    # Get face encodings for any faces in the uploaded image
    unknown_face_encodings = face_recognition.face_encodings(img)
    return unknown_face_encodings

@app.route('/api/persons', methods=["GET"])
def get_games():
    games = person_controller.get_games()
    return jsonify(games)

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
    # image_encodings = detect_faces_in_image
    message = person_details["message"]
    result = person_controller.insert_game(name, message)
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
    return jsonify(person)


if __name__ == "__main__":
    create_tables()
    """
    Here you can change debug and port
    Remember that, in order to make this API functional, you must set debug in False
    """
    app.run(host='0.0.0.0', port=8000, debug=False)
