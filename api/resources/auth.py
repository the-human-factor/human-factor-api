import structlog
from datetime import datetime

from flask import request, abort, current_app
from flask_restful import Resource

import api.models as m
import api.schemas as s


from flask_jwt_extended import (
  JWTManager,
  jwt_required,
  get_raw_jwt,
  get_jwt_identity,
  jwt_refresh_token_required)

jwt = JWTManager()
logger = structlog.get_logger()

class UserRegister(Resource):
  def post(self):
    try:
      json = request.get_json()
      full_name = json['fullName']
      email = json['email']
      password = json['password']
    except (KeyError, AttributeError) as e:
      logger.error(event="Request missing values")
      abort(400)

    user = m.User.query.filter_by(email=email).one_or_none()

    if user:
      return {
          'error': 'EmailExists',
          'message': 'User already exists. Please log in.',
      }, 409

    user = m.User.create(full_name=full_name,
                         email=email,
                         password=password)

    return {
        'access_token': user.create_access_token_with_claims(),
        'refresh_token': user.create_refresh_token(),
        'user': s.UserSchema().jsonify(user).json
    }, 201

class UserPassword(Resource):
  @jwt_required
  def put(self):
    try:
      json = request.get_json()
      old_password = json['oldPassword']
      new_password = json['password']
    except (KeyError, AttributeError) as e:
      log.error("Request missing values")
      abort(400)

    user = m.User.query.get(get_jwt_identity())

    if not user.check_password(old_password):
      return {
        'error': 'IncorrectPassword',
        'message': 'Incorrect password supplied when changing passwords'
      }, 400

    user.update(password=new_password)

    return {
      'access_token': user.create_access_token_with_claims(),
      'refresh_token': user.create_refresh_token()
    }, 200

class UserLogin(Resource):
  def post(self):
    try:
      json = request.get_json()
      username = json['email']
      password = json['password']
    except (KeyError, AttributeError) as e:
      print("Request missing values")
      abort(400)

    user = m.User.query.filter_by(email=username).first()

    if user and user.check_password(password):
      ret = {
          'access_token': user.create_access_token_with_claims(),
          'refresh_token': user.create_refresh_token(),
          'user': s.UserSchema().jsonify(user).json
      }
      return ret, 200

    return {
      'error': 'AuthenticationFailure',
      'message': 'Unknown user or incorrect password'
    }, 401


class UserRefresh(Resource):
  @jwt_refresh_token_required
  def post(self):
    user_id = get_jwt_identity()
    user = m.User.query.get(user_id)
    return {
        'access_token': user.create_access_token_with_claims(),
        'user': s.UserSchema().jsonify(user).json
    }, 200

class UserLogout(Resource):
  @jwt_refresh_token_required
  def get(self):
    token = get_raw_jwt()
    jti = token['jti']
    exp = token['exp']
    blacklisted_token = m.BlacklistedToken.create(
      jti=jti,
      exp=datetime.utcfromtimestamp(exp))

    return 201


@jwt.token_in_blacklist_loader
def check_if_token_in_blacklist(decrypted_token):
  row = m.BlacklistedToken.query.get(decrypted_token['jti'])
  return bool(row)
