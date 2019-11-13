from flask import request, abort
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity

import api.models as m
import api.schemas as s
from api.auth import is_admin, abortUnauthorized


class Response(Resource):
  @jwt_required
  def get(self, response_id):
    response = m.Response.query.get_or_404(response_id)

    if response.sequence_response is not None:
      if response.sequence_response.hidden_from_respondent and not is_admin():
        abortUnauthorized()

    if not is_admin() and response.user_id is not get_jwt_identity():
      abortUnauthorized()

    return s.ResponseSchema().jsonify(response).json, 200


class ResponseList(Resource):
  @jwt_required
  def get(self):
    if is_admin():
      responses = m.Response.all()
    else:
      responses = m.Response.where(user_id=get_jwt_identity()).all()

    return s.ResponseSchema(many=True).jsonify(responses).json, 200


class CreateResponse(Resource):
  @jwt_required
  def post(self):
    user = m.User.query.get(get_jwt_identity())
    try:
      challenge_id = request.form["challengeId"]
      video_blob = request.files["videoBlob"]
    except (KeyError, AttributeError) as e:
      abort(400, "Request missing values")

    video = m.Video().create_and_upload(video_blob)
    challenge = m.Challenge.query.get_or_404(challenge_id)

    response = m.Response.create(challenge=challenge, user=user, video=video)

    return s.ResponseSchema().jsonify(response).json, 201
