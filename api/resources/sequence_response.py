from flask import request, abort
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity

import api.models as m
import api.schemas as s


class SequenceResponse(Resource):
  @jwt_required
  def get(self, sequence_response_id):
    sequence_response = m.SequenceResponse.query.get_or_404(sequence_response_id)

    # TODO: Get all the responses that are required

    return s.SequenceResponseSchema().jsonify(sequence_response).json, 200


class SequenceResponseList(Resource):
  @jwt_required
  def get(self):
    sequence_responses = m.SequenceResponse.all()

    return s.SequenceResponseSchema(many=True).jsonify(sequence_responses).json, 200


class CreateSequenceResponse(Resource):
  @jwt_required
  def post(self):
    user = m.User.query.get(get_jwt_identity())
    try:
      sequence_id = request.form["sequenceId"]
    except (KeyError, AttributeError) as e:
      print("Request sequence_id")
      abort(400)

    sequence_response = m.SequenceResponse.create(sequence_id=sequence_id)

    return s.SequenceResponseSchema().jsonify(sequence_response).json, 201
