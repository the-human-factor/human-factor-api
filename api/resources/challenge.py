import structlog

from jsonpatch import JsonPatch
from flask import request, abort
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity

from sqlalchemy.orm import joinedload

import api.models as m
import api.schemas as s

from api.auth import admin_required, is_admin

log = structlog.get_logger()


class Challenge(Resource):
  @jwt_required
  def get(self, challenge_id):
    challenge = m.Challenge.query.get_or_404(challenge_id)
    return s.ChallengeSchema().jsonify(challenge).json, 200

  @admin_required
  def put(self, challenge_id):
    try:
      patch = JsonPatch(request.get_json(force=True))
    except (KeyError, AttributeError) as e:
      log("Request missing values")
      abort(400)

    schema = s.ChallengeSchema()
    challenge = m.Challenge.query.get_or_404(challenge_id)
    data = schema.dump(challenge)

    new_data = patch.apply(data)
    schema.load(new_data, instance=challenge).save()

    return new_data, 200


class CreateChallenge(Resource):
  @jwt_required
  def post(self):
    user = m.User.query.get(get_jwt_identity())

    try:
      title = request.form["title"]
      instructions = request.form["instructions"]
      grading_notes = request.form["gradingNotes"]
      video_blob = request.files["videoBlob"]
    except (KeyError, AttributeError) as e:
      log.info("Request missing values")
      abort(400)

    video = m.Video().create_and_upload(video_blob)

    challenge = m.Challenge.create(
      title=title,
      instructions=instructions,
      grading_notes=grading_notes,
      user=user,
      video=video,
    )

    return s.ChallengeSchema().jsonify(challenge).json, 201


class ChallengeList(Resource):
  @jwt_required
  def get(self):
    user = m.User.query.get(get_jwt_identity())
    if is_admin():
      challenges = m.Challenge.query.options(
        joinedload("video"), joinedload("user")
      ).all()

    else:
      challenges = (
        m.Challenge.query.filter(
          (m.Challenge.listed == True) | (m.Challenge.user_id == get_jwt_identity())
        )
        .options(joinedload("video"), joinedload("user"))
        .all()
      )

    return s.ChallengeSchema(many=True).jsonify(challenges).json, 200
