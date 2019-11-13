from flask import request, abort
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity

import api.models as m
import api.schemas as s
from api.auth import is_admin


class SequenceResponse(Resource):
  @jwt_required
  def get(self, sequence_response_id):
    sequence_response = m.SequenceResponse.query.get_or_404(sequence_response_id)

    if s.sequence_response.hide_responses and not is_admin():
      return (
        s.SequenceResponseHiddenResponsesSchema().jsonify(sequence_response).json,
        200,
      )
    else:
      return s.SequenceResponseSchema().jsonify(sequence_response).json, 200


class SequenceResponseList(Resource):
  @jwt_required
  def get(self):
    if is_admin():
      sequence_responses = m.SequenceResponse.all()
      return s.SequenceResponseSchema(many=True).jsonify(sequence_responses).json, 200
    else:
      sequence_responses = m.SequenceResponse.where(user_id=get_jwt_identity()).all()
      return (
        s.SequenceResponseHiddenResponsesSchema(many=True)
        .jsonify(sequence_responses)
        .json,
        200,
      )


class CreateSequenceResponseInvite(Resource):
  @jwt_required
  def post(self):
    try:
      email = request.form["email"]
      full_name = request.form["fullName"]
      sequence_id = request.form["sequenceId"]
      hide_responses = request.form["hideResponses"]
    except (KeyError, AttributeError) as e:
      abort(400, "Missing expected form values")

    user = m.User.query.filter_by(email=email).one_or_none()

    if user is None:
      # TODO create a good fake password
      user = m.User.create(full_name=full_name, email=email, password="temp_password")

    sequence_response = m.SequenceResponse.create(
      sequence_id=sequence_id, hide_responses=hide_responses, user=user
    )

    # TODO: Send an email invite?

    return (
      s.SequenceResponseHiddenResponsesSchema().jsonify(sequence_response).json,
      201,
    )


class StartSequenceResponse(Resource):
  @jwt_required
  def post(self):
    user = m.User.query.get(get_jwt_identity())

    try:
      sequence_id = request.form["sequenceId"]
    except (KeyError, AttributeError) as e:
      abort(400, "Missing expected form values")

    sequence_response = m.SequenceResponse.create(
      sequence_id=sequence_id, hide_responses=False, user=user
    )

    return (
      s.SequenceResponseHiddenResponsesSchema().jsonify(sequence_response).json,
      201,
    )


class RespondToSequenceResponse(Resource):
  @jwt_required
  def post(self):
    user = m.User.query.get(get_jwt_identity())
    try:
      challenge_id = request.form["challengeId"]
      items_finished = request.form["itemsFinished"]
      sequence_response_id = request.form["sequenceResponseId"]
      video_blob = request.files["videoBlob"]
    except (KeyError, AttributeError) as e:
      abort(400, "Request missing values")

    video = m.Video().create_and_upload(video_blob)
    challenge = m.Challenge.query.get_or_404(challenge_id)
    sequence_response = m.Challenge.query.get_or_404(sequence_response_id)

    response = m.Response.create(
      challenge=challenge,
      user=user,
      video=video,
      sequence_responses=[sequence_response],
    )

    finished = items_finished >= sequence_response.items_finished - 1
    sequence_response.update(items_finished=items_finished, finished=finished)

    return "Ok", 201
