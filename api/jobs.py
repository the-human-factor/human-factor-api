import os
import uuid
import ffmpeg
import subprocess
import structlog
from dynaconf import settings
from flask_rq2 import RQ

import api.models as m
from api.ffmpeg import encode_mp4

rq = RQ()
logger = structlog.get_logger()


@rq.job(timeout=settings.get("ENCODING_TASK_TIMEOUT"))
def ingest_video(video_id, req_id="00" + str(uuid.uuid4())):
  log = logger.new(request_id=req_id, video_id=video_id)
  log.info("Video encoding started")

  video = m.Video.where(id=video_id).one_or_none()
  video.ingest_source_from_bucket()

  log.info("Video encoding finished")


@rq.job
def ingest_local_video(output_name):
  reencoded_path = f"{output_name}.mp4"
  source_path = "./api/tests/data/test.webm"

  encode_mp4(source_path, reencoded_path)

  print("ENCODING DONE!!!")


@rq.job
def ingest_local_video2(output_name):
  reencoded_path = f"{output_name}.mp4"
  source_path = "./api/tests/data/test2.webm"

  ffmpeg.input(source_path).output(reencoded_path, vcodec="libx264", vsync="2").run(
    overwrite_output=True
  )

  print("ENCODING DONE!!!")
