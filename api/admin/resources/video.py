import structlog

from flask_restful import Resource

from api.models import Video
from api.jobs import ingest_video
from api.auth import super_admin_required

log = structlog.get_logger()


class VideoEncode(Resource):
    @super_admin_required
    def post(self, video_id):
        video = Video.query.get_or_404(video_id)
        log.info("Enqueueing for encoding", video_id=video.id)
        ingest_video.delay(video.id)

        return "ok", 201


class VideoEncodeAll(Resource):
    @super_admin_required
    def post(self):
        for video in Video.where(encoded_at=None):
            log.info("Enqueueing for encoding", video_id=video.id)
            ingest_video.delay(video.id)

        return "ok", 201
