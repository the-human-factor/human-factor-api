import os
import subprocess
import structlog
import functools
from PIL import Image

log = structlog.get_logger()


@functools.lru_cache(maxsize=None)
def info(input_path):
  args = [
    "ffprobe",
    "-hide_banner",
    "-v",
    "error",
    "-show_entries",
    "stream=width,height,duration",
    "-of",
    "default=noprint_wrappers=1:nokey=1",
    "-select_streams",
    "V",
    input_path,
  ]

  out = subprocess.check_output(args)  # shell=true will cause the cmd to fail.
  out = out.decode("utf-8").split("\n")
  return {"width": int(out[0]), "height": int(out[1]), "duration": float(out[2])}


#
# FFMPEF H.264 settings:
# https://trac.ffmpeg.org/wiki/Encode/H.264
def encode_mp4(input_path, output_path, crf="17", speed="slower"):
  """Encodes a source input video into a mp4 with h264 encoding.
  Raises:
    subprocess.CalledProcessError: When the ffmpeg command fails.
  """
  args = [
    "ffmpeg",
    "-hide_banner",
    "-y",
    "-i",
    input_path,
    "-c:v",
    "libx264",
    "-crf",
    crf,
    "-preset",
    speed,
    "-loglevel",
    "debug",
    "-vsync",
    "2",  # http://ffmpeg.org/pipermail/ffmpeg-user/2018-May/039926.html
    "-movflags",
    "+faststart",
    output_path,
  ]

  log.info("Running ffmpeg with options", args=args)

  subprocess.check_call(args)


def capture_still(input_path, output_path, at_time=0.0):
  args = [
    "ffmpeg",
    "-hide_banner",
    "-y",
    "-ss",
    str(at_time),  # start time is in seconds
    "-i",
    input_path,
    "-vframes",
    "1",
    "-f",
    "image2",
    output_path,
  ]
  subprocess.check_call(args)


def resize_image(input_path, output_path, width=200):
  with Image.open(input_path) as img:
    height = int(float(img.size[1]) * (width / float(img.size[0])))
    img.thumbnail((width, height), Image.ANTIALIAS)
    img.save(output_path)
