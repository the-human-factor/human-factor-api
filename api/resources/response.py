from flask import request, abort
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.orm import joinedload

import api.models as m
import api.schemas as s


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
