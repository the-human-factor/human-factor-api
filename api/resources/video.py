import structlog

from flask import request, abort
from flask_restful import Resource
from flask_jwt_extended import jwt_required

import api.models as m
import api.schemas as s

log = structlog.get_logger()


class Video(Resource):
  @jwt_required
  def get(self, video_id):
    video = m.Video.query.get_or_404(video_id)
    return s.VideoSchema().jsonify(video).json, 200


class CreateVideo(Resource):
  @jwt_required
  def post(self):
    if "videoBlob" not in request.files:
      log("Request missing value for 'videoBlob'")
      abort(400)

    video_blob = request.files["videoBlob"]
    video = m.Video.create_and_upload(video_blob)
    return s.VideoSchema().jsonify(video).json, 201
