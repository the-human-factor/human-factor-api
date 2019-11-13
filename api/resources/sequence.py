from flask import request, abort
from flask_restful import Resource
from flask_jwt_extended import jwt_required
from sqlalchemy.exc import DataError
import json

import api.models as m
import api.schemas as s
from api.auth import is_admin


class Sequence(Resource):
  @jwt_required
  def get(self, sequence_id):
    sequence = m.Sequence.query.get_or_404(sequence_id)

    if is_admin():
      return s.SequenceSchema().jsonify(sequence).json, 200
    else:
      return s.SequenceHiddenResponsesSchema().jsonify(sequence).json, 200


class SequenceList(Resource):
  @jwt_required
  def get(self):
    sequences = m.Sequence.all()

    if is_admin():
      return s.SequenceSchema(many=True).jsonify(sequences).json, 200
    else:
      return s.SequenceHiddenResponsesSchema(many=True).jsonify(sequences).json, 200


class CreateSequence(Resource):
  @jwt_required
  def post(self):
    try:
      title = request.form["title"]
      items_json = request.form["itemsJson"]
    except (KeyError, AttributeError) as e:
      print(e)
      abort(402, "Request missing values")

    try:
      items = json.loads(items_json)
    except json.JSONDecodeError as e:
      abort(400, "invalid json")

    try:
      videos = []
      challenges = []
      for item in items:
        if item.get("type") == "video":
          videos.append(m.Video.query.get(item["video_id"]))
        elif item.get("type") == "challenge":
          challenges.append(m.Challenge.query.get(item["challenge_id"]))
    except DataError:
      abort(400, "Invalid challenge or video id")

    sequence = m.Sequence.create(
      title=title,
      items_json=items_json,
      items_length=len(items),
      videos=videos,
      challenges=challenges,
    )

    return s.SequenceSchema().jsonify(sequence).json, 201
