import structlog

from jsonpatch import JsonPatch
from flask import request, abort
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity

from sqlalchemy.orm import joinedload
from sqlalchemy.sql import func

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

  @admin_required
  def delete(self, challenge_id):
    challenge = m.Challenge.query.get_or_404(challenge_id)
    challenge.update(listed=False, deleted_at=func.now())
    return None, 200


class CreateChallenge(Resource):
  @jwt_required
  def post(self):
    user = m.User.query.get(get_jwt_identity())

    try:
      title = request.form["title"]
      instructions = request.form["instructions"]
      video_blob = request.files["videoBlob"]
    except (KeyError, AttributeError) as e:
      log.info("Request missing values", error=e)
      abort(400)
    grading_notes = request.form.get("gradingNotes", "")

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
      challenges = (
        m.Challenge.query.filter(m.Challenge.deleted_at.is_(None))
        .options(joinedload("video"), joinedload("user"))
        .order_by(m.Challenge.listed.desc())
        .all()
      )

    else:
      challenges = (
        m.Challenge.query.filter(
          m.Challenge.deleted_at.is_(None) & (m.Challenge.listed == True)
          | (m.Challenge.user_id == get_jwt_identity())
        )
        .options(joinedload("video"), joinedload("user"))
        .all()
      )

    return s.ChallengeSchema(many=True).jsonify(challenges).json, 200
