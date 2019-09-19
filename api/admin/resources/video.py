import structlog

from flask import request
from flask_restful import Resource
from flask_jwt_extended import jwt_required

from api.models import Video
from api.jobs import ingest_video

log = structlog.get_logger()

class VideoEncodeAll(Resource):
  @jwt_required
  def post(self):
    for video in Video.where(encoded_at=None):
      log.info("Enqueueing for encoding", video_id=video.id)
      ingest_video(video.id)

    return 'ok', 201
