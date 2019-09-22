import uuid
import structlog
from dynaconf import settings
from flask_rq2 import RQ

import api.models as m

rq = RQ()
logger = structlog.get_logger()

@rq.job(timeout=settings.get('ENCODING_TASK_TIMEOUT'))
def ingest_video(video_id, req_id='00' + str(uuid.uuid4())):
  log = logger.new(request_id=req_id, video_id=video_id)
  log.info("Video encoding started")

  video = m.Video.where(id=video_id).one_or_none()
  video.ingest_source_from_bucket()

  log.info("Video encoding finished")
