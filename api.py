from flask import Flask, request, jsonify
import json
from cores.db import DatabaseAPI

# init Flask application
app = Flask(__name__)

# Simple Endpoint to return Hello world message
@app.route("/hello", methods=["GET"])
def home():
    return "Hello World!"

@app.route("/books", methods=["GET"])
def get_all_books() -> list:
    database_api = DatabaseAPI("booksDB.db")
    response = {
        "data":{
            "result": database_api.get_all_books()
        }
    }
    return response

@app.route("/books/<id>", methods=["GET"])
def get_book_by_id(id: int) -> str:
    database_api = DatabaseAPI("booksDB.db")
    result = list(database_api.get_book_by_id(id))
    response = {
        "data":{
            "result": result[0]
        }
    }
    return response

@app.route("/books", methods=["POST"])
def add_new_book() -> str:
    database_api = DatabaseAPI("booksDB.db")
    # Reading request body data in json format
    request_body = json.loads(request.data.decode())
    new_book = {
        "title": request_body["title"],
        "author": request_body["author"],
        "description": request_body["description"],
        "pages": request_body["pages"],
    }
    # Add book to database
    database_api.insert_book(new_book)
    return jsonify(new_book)

@app.route("/books/<id>", methods=["PUT"])
def update_book(id: int) -> str:
    database_api = DatabaseAPI("booksDB.db")
    # Reading request body data in json format
    request_body = json.loads(request.data.decode())
    new_book = {
        "title": request_body["title"],
        "author": request_body["author"],
        "description": request_body["description"],
        "pages": request_body["pages"],
    }
    # Add book to database
    database_api.update_book(id, new_book)
    return jsonify(new_book)

@app.route("/books/<id>", methods=["DELETE"])
def delete_book(id: int) -> str:
    database_api = DatabaseAPI("booksDB.db")
    # Reading request body data in json format
    selected_book = list(database_api.get_book_by_id(id))
    response = {
        "data":{
            "result": selected_book[0]

        }
    }
    database_api.delete_book(id)
    return response

# Running your application with debugging mode on
app.run(debug=True)
