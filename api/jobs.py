import uuid

import structlog

from celery import Celery

from api.app import db
from api.utils import get_redis_url

from dynaconf import LazySettings

settings = LazySettings(ENVVAR_PREFIX_FOR_DYNACONF="FLASK")
# ENVVAR_FOR_DYNACONF=ENVVAR_FOR_DYNACONF,
# ENV_SWITCHER_FOR_DYNACONF=ENV_SWITCHER_FOR_DYNACONF

logger = structlog.get_logger()

redis_url = get_redis_url(settings)
logger.info("Worker connecting to redis", redis_url=redis_url, env=settings["ENV"])

celery = Celery(__name__, broker=redis_url, backend=redis_url)


@celery.task
def ingest_video(video_id, req_id="00" + str(uuid.uuid4())):
  import api.models as m

  log = logger.new(request_id=req_id, video_id=video_id)
  log.info("Video encoding started")

  video = m.Video.where(id=video_id).one_or_none()
  video.ingest_source_from_bucket()
  db.session.commit()

  log.info("Video encoding finished")
