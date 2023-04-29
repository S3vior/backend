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

engine = create_engine('sqlite:///savior.db', echo=True)
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
        user.token=access_token
        return jsonify({'access_token': access_token}), 200
    else:
        return jsonify({'message': 'Invalid user name or password'}), 401



# --------------------------------change passward--------------------------------------------


@auth_app.route('/api/change_password', methods=['POST'])
@jwt_required()  # Requires authentication with a JWT token
def change_password():
    current_user_id = get_jwt_identity()  # Get the current user from the token
    # Query the database for the user
    user = session.query(User).filter_by(id=current_user_id).first()

    # Get the old password, new password, and confirmation of new password from the request body
    old_password = request.json.get('old_password')
    new_password = request.json.get('new_password')
    confirm_password = request.json.get('confirm_password')

    # Check if the old password is correct
    if  user.password != old_password:
        return jsonify({'message': 'Old password is incorrect.'}), 400

    # Check if the new password and confirmation match
    if new_password != confirm_password:
        return jsonify({'message': 'New password and confirmation do not match.'}), 400

    user.password = new_password
    session.commit()

    return jsonify({'message': 'Password updated successfully.'}), 200
# ----------------------------------------------------------------------------


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
