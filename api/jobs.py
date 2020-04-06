import uuid

import structlog

from celery import Celery

from api.utils import get_redis_url

redis_url = get_redis_url()

celery = Celery(__name__, broker=redis_url, backend=redis_url)
logger = structlog.get_logger()


@celery.task
def ingest_video(video_id, req_id="00" + str(uuid.uuid4())):
  import api.models as m

  log = logger.new(request_id=req_id, video_id=video_id)
  log.info("Video encoding started")

  video = m.Video.where(id=video_id).one_or_none()
  video.ingest_source_from_bucket()

  log.info("Video encoding finished")
