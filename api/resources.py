import os
import json
from datetime import datetime

from sqlalchemy.orm import joinedload
from flask import request, abort, jsonify, current_app
from flask_restful import Resource
from flask_jwt_extended import (
    jwt_required, create_access_token, create_refresh_token,
    get_jwt_identity, jwt_refresh_token_required, JWTManager,
    get_raw_jwt
  )

import api.models as m
import api.schemas as s

jwt = JWTManager()

@jwt.token_in_blacklist_loader
def check_if_token_in_blacklist(decrypted_token):
  jti = decrypted_token['jti']
  row = m.BlacklistedToken.query.get(decrypted_token['jti'])
  return bool(row)

def create_access_token_with_claims(user_id):
  # TODO: Implement claims
  claims = {'roles': [{'admin': 'admin'},]}
  return create_access_token(identity=user_id, user_claims=claims)

class UserRegister(Resource):
  def post(self):
    json = request.get_json()
    full_name = json.get('fullName')
    email = json.get('email')
    password = json.get('password')
    user = m.User.query.filter_by(email=email).one_or_none()

    if user:
      return {
          'error': 'EmailExists',
          'message': 'Email already exists.',
      }, 409

    user = m.User(full_name=full_name,
                  email=email,
                  password=password)
    user.save()

    return {
        'access_token': create_access_token_with_claims(user.id),
        'refresh_token': create_refresh_token(identity=user.id),
        'user': s.UserSchema().jsonify(user).json
    }, 200


class UserLogin(Resource):
  def post(self):
    json = request.get_json()
    username = json.get('email')
    password = json.get('password')

    user = m.User.query.filter_by(email=username).first()

    if user and user.check_password(password):
      ret = {
          'access_token': create_access_token_with_claims(user.id),
          'refresh_token': create_refresh_token(identity=user.id),
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
        'access_token': create_access_token_with_claims(user_id),
        'user': s.UserSchema().jsonify(user).json
    }, 200


class UserLogout(Resource):
  @jwt_refresh_token_required
  def post(self):
    token = get_raw_jwt()
    jti = token['jti']
    exp = token['exp']
    blacklisted_token = m.BlacklistedToken(
        jti = jti,
        exp = datetime.utcfromtimestamp(exp)
    )
    blacklisted_token.save()

    return {}, 200


class Video(Resource):
  @jwt_required
  def get(self, video_id):
    video = m.Video.query.get_or_404(video_id)
    return s.VideoSchema().jsonify(video).json, 200


class CreateVideo(Resource):
  @jwt_required
  def post(self):
    video_blob = request.files['videoBlob']
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

    title = request.form['title']
    instructions = request.form['instructions']
    grading_notes = request.form['gradingNotes']
    video_blob = request.files['videoBlob']

    video = m.Video().create_and_upload(video_blob)

    challenge = m.Challenge(
      title = title,
      instructions = instructions,
      grading_notes = grading_notes,
      user = user,
      video = video
    )

    challenge.save()

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
    challenge_id = request.form['challengeId']
    video_blob = request.files['videoBlob']

    video = m.Video().create_and_upload(video_blob)
    challenge = m.Challenge.query.get_or_404(challenge_id)

    video = m.Video().create_and_upload(video_blob)
    challenge = m.Challenge.query.get_or_404(challenge_id)

    response = m.Response.create(
      challenge=challenge,
      user=user,
      video=video)

    return s.ResponseSchema().jsonify(response).json, 201
