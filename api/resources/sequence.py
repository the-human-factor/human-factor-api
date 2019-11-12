from flask import request, abort
from flask_restful import Resource
from flask_jwt_extended import jwt_required

import api.models as m
import api.schemas as s


class Sequence(Resource):
  @jwt_required
  def get(self, sequence_id):
    sequence = m.Sequence.query.get_or_404(sequence_id)

    # TODO: Get all the videos and challenges that are required

    return s.SequenceSchema().jsonify(sequence).json, 200


class SequenceList(Resource):
  @jwt_required
  def get(self):
    sequences = m.Sequence.all()

    return s.SequenceSchema(many=True).jsonify(sequences).json, 200


class CreateSequence(Resource):
  @jwt_required
  def post(self):
    try:
      title = request.form["title"]
      items_json = request.form["itemsJson"]
    except (KeyError, AttributeError) as e:
      print("Request missing values")
      abort(400)

    sequence = m.Sequence.create(title=title, items_json=user)

    return s.SequenceSchema().jsonify(sequence).json, 201
