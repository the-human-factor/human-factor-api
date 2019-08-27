from flask import request, abort
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity

from sqlalchemy.orm import joinedload

import api.models as m
import api.schemas as s


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
