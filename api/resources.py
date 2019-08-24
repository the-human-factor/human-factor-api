import os
import json
from datetime import datetime

from sqlalchemy.orm import joinedload
from flask import request, abort, jsonify, current_app
from flask_restful import Resource
from flask_jwt_extended import (
  jwt_required, get_jwt_identity,
  jwt_refresh_token_required, JWTManager, get_raw_jwt)

import api.models as m
import api.schemas as s

jwt = JWTManager()

class UserRegister(Resource):
  def post(self):
    try:
      json = request.get_json()
      full_name = json.get('full_name')
      email = json.get('email')
      password = json.get('password')
    except (KeyError, AttributeError) as e:
      print("Request missing values")
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
        'user': s.UserSchema().dump(user)
    }, 201


class UserLogin(Resource):
  def post(self):
    try:
      json = request.get_json()
      username = json.get('email')
      password = json.get('password')
    except (KeyError, AttributeError) as e:
      print("Request missing values")
      abort(400)

    user = m.User.query.filter_by(email=username).first()

    if user and user.check_password(password):
      ret = {
          'access_token': user.create_access_token_with_claims(),
          'refresh_token': user.create_refresh_token(),
          'user': s.UserSchema().dump(user)
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
        'user': s.UserSchema().dump(user)
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


class Video(Resource):
  @jwt_required
  def get(self, video_id):
    video = m.Video.query.get_or_404(video_id)
    return s.VideoSchema().jsonify(video).json, 200


class CreateVideo(Resource):
  @jwt_required
  def post(self):
    if 'video_blob' not in request.files:
      print("Request missing values")
      abort(400)

    video_blob = request.files['video_blob']
    video = m.Video.create_and_upload(video_blob)
    return s.VideoSchema().jsonify(video).json, 201


class Challenge(Resource):
  @jwt_required
  def get(self, challenge_id):
    challenge = m.Challenge.query.get_or_404(challenge_id)
    return s.ChallengeSchema().jsonify(challenge).json, 200

class CreateChallenge(Resource):
  @jwt_required
  def post(self):
    user = m.User.query.get(get_jwt_identity())

    try:
      title = request.form['title']
      instructions = request.form['instructions']
      grading_notes = request.form['grading_notes']
      video_blob = request.files['video_blob']
    except (KeyError, AttributeError) as e:
      print("Request missing values")
      abort(400)

    video = m.Video().create_and_upload(video_blob)

    challenge = m.Challenge.create(
      title=title,
      instructions=instructions,
      grading_notes=grading_notes,
      user=user,
      video=video)

    return s.ChallengeSchema().jsonify(challenge).json, 201

class ChallengeList(Resource):
  @jwt_required
  def get(self):
    user = m.User.query.get(get_jwt_identity())
    challenges = m.Challenge.query.options(joinedload('video'), joinedload('user')).all()

    return s.ChallengeSchema(many=True).jsonify(challenges).json, 200

class Response(Resource):
  @jwt_required
  def get(self, response_id):
    response = m.Response.query.get_or_404(response_id)

    return s.ResponseSchema().jsonify(response).json, 200

class ResponseList(Resource):
  @jwt_required
  def get(self):
    responses = m.Response.query.options(
      joinedload('challenge'),
      joinedload('user'),
      joinedload('video')
    ).all()

    return s.ResponseSchema(many=True).jsonify(responses).json, 200


class CreateResponse(Resource):
  @jwt_required
  def post(self):
    user = m.User.query.get(get_jwt_identity())

    try:
      challenge_id = request.form['challenge_id']
      video_blob = request.files['video_blob']
    except (KeyError, AttributeError) as e:
      print("Request missing values")
      abort(400)

    video = m.Video().create_and_upload(video_blob)
    challenge = m.Challenge.query.get_or_404(challenge_id)

    response = m.Response.create(
      challenge=challenge,
      user=user,
      video=video)

    return s.ResponseSchema().jsonify(response).json, 201
