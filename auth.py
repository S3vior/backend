from flask import Flask, jsonify, request, redirect, render_template,  make_response ,Blueprint
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from sqlalchemy import create_engine

from models import User

from flask_jwt_extended import (
    JWTManager, jwt_required, create_access_token,
    get_jwt_identity
)


app = Flask(__name__)

auth_app = Blueprint('auth', __name__)
jwt = JWTManager(app)

engine = create_engine('sqlite:///missing_persons.db', echo=True)
Session = sessionmaker(bind=engine)

# create a session
session = Session()

# define the authentication endpoints
@auth_app.route('/api/auth/register', methods=['POST'])
def register():
    # get user data from request
    user_data = request.get_json()

    # create a new user object
    user = User(
        user_name=user_data['user_name'],
        phone_number=user_data['phone_number'],
        password=user_data['password']
    )

    # add the user object to the database
    try:
        session = Session()
        session.add(user)
        session.commit()
        return jsonify({'message': 'User created successfully'}), 201
    except IntegrityError:
        session.rollback()
        return jsonify({'message': 'User already exists'}), 400
    finally:
        session.close()

@auth_app.route('/api/auth/login', methods=['POST'])
def login():
    # get user credentials from request
    user_data = request.get_json()
    user_name = user_data['user_name']
    password = user_data['password']

    # query the user from the database
    session = Session()
    user = session.query(User).filter_by(user_name=user_name).first()
    session.close()

    # check if the user exists and the password matches
    if user and user.password == password:
        # generate an access token
        access_token = create_access_token(identity=user.id)
        return jsonify({'access_token': access_token}), 200
    else:
        return jsonify({'message': 'Invalid user name or password'}), 401

@auth_app.route('/api/profile', methods=['GET'])
@jwt_required()
def get_user():
    # get the user id from the access token
    user_id = get_jwt_identity()

    # query the user from the database
    session = Session()
    user = session.query(User).get(user_id)
    session.close()

    # return the user data
    return jsonify({
        'id': user.id,
        'user_name': user.user_name,
        'phone_number': user.phone_number,
    }), 200
