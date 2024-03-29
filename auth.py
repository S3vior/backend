from flask import Flask, jsonify, request, redirect, render_template,  make_response ,Blueprint
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError ,SQLAlchemyError
from sqlalchemy import create_engine
import json
from models import User

from flask_jwt_extended import (
    JWTManager, jwt_required, create_access_token,get_jwt,unset_jwt_cookies,
    get_jwt_identity
)


app = Flask(__name__)

auth_app = Blueprint('auth', __name__)
jwt = JWTManager(app)

# Create a blacklist to store revoked tokens
blacklist = set()
engine = create_engine('sqlite:///savior.db', echo=True)
Session = sessionmaker(bind=engine)

# create a session
session = Session()


@auth_app.route('/api/users/update_token', methods=['POST'])
@jwt_required()
def update_fcm_token():
    current_user = get_jwt_identity()
    fcm_token = request.json.get('fcm_token')

    user = session.query(User).filter_by(id=current_user).first()
    if user:
        user.fcm_token = fcm_token
        session.commit()
        return {'message': 'FCM token updated successfully'}
    else:
        return {'message': 'User not found'}, 404

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
        access_token = create_access_token(identity=user.id, additional_claims={'logged_out': False})
        user.token=access_token
        session.commit()
        return jsonify({'access_token': access_token}), 200
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
        access_token = create_access_token(identity=user.id, additional_claims={'logged_out': False})
        user.token=access_token
        session.commit()
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


@auth_app.route('/api/users/<int:user_id>/profile', methods=['GET'])
def get_user_profile(user_id):
    # query the user from the database
    session = Session()
    user = session.query(User).get(user_id)
    session.close()

    if user is None:
        return jsonify({'message': 'User not found'}), 404

    # return the user data
    return jsonify({
        'id': user.id,
        'user_name': user.user_name,
        'phone_number': user.phone_number,
    }), 200
@auth_app.route('/users/<int:user_id>', methods=['PUT'])
def edit_user_profile(user_id):
    # Retrieve the request data
    data = request.get_json()

    # Start a new database session
    session = Session()

    try:
        # Retrieve the user from the database
        user = session.query(User).filter(User.id == user_id).first()

        if not user:
            return jsonify({'error': 'User not found'}), 404

        # Update the user's profile
        user.user_name = data.get('user_name', user.user_name)
        user.phone_number = data.get('phone_number', user.phone_number)
        user.password = data.get('password', user.password)

        # Commit the changes to the database
        session.commit()

        # Return the updated user profile
        return jsonify({'message': 'User profile updated successfully', 'user': user.__repr__()})

    except SQLAlchemyError as e:
        # Handle any database errors
        session.rollback()
        return jsonify({'error': str(e)}), 500

    finally:
        # Close the database session
        session.close()
@auth_app.route('/api/users', methods=["GET"])
def get_users():
    users = session.query(User).all()

    # convert persons to JSON
    users_json = json.dumps([{
        'id': user.id,
        'name': user.user_name,
        'phone_number':user.phone_number,
        'fcm_token': user.fcm_token,
        'token' : user.token,
        'password' : user.password
    } for user in users])

    # return JSON response
    return users_json


@jwt.expired_token_loader
def handle_expired_token_callback():
    # Check the custom claim to determine if the user logged out
    logged_out = get_jwt()['logged_out']
    if logged_out:
        return jsonify({'message': 'Token expired after logout'}), 401
    else:
        return jsonify({'message': 'Token has expired'}), 401

@auth_app.route('/api/auth/logout', methods=['POST'])
@jwt_required()
def logout():
    # Revoke the current user's token
    unset_jwt_cookies()
    return jsonify({'message': 'Successfully logged out'}), 200
