import os
import subprocess
import tempfile
import functools
import shutil
import Image

# FFMPEF H.264 settings:
# https://trac.ffmpeg.org/wiki/Encode/H.264
#
# CRF
# The range of the CRF scale is 0–51, where 0 is lossless, 23 is the default,
# and 51 is worst quality possible. A lower value generally leads to higher
# quality, and a subjectively sane range is 17–28. Consider 17 or 18 to be
# visually lossless or nearly so; it should look the same or nearly the same
# as the input but it isn't technically lossless.
#
# The range is exponential, so increasing the CRF value +6 results in roughly
# half the bitrate / file size, while -6 leads to roughly twice the bitrate.

# Compatibility
# -profile:v high -level 4.0
# Apple TV 3 and later, iPad 2 and later, iPhone 4s and later

# Going from medium to slow, the time needed increases by about 40%. Going to
# slower instead would result in about 100% more time needed (i.e. it will take
# twice as long). Compared to medium, veryslow requires 280% of the original
# encoding time, with only minimal improvements over slower in terms of quality.

def initTempDir(parent, name):
  directory = os.path.join(parent, name)
  if os.path.exists(directory):
    shutil.rmtree(directory)
  os.makedirs(directory)
  return directory


class FFMPEG:
  def __init__(self):
    self.upload_video_dir = None
    self.output_video_dir = None
    self.output_image_dir = None

  def initDirs(self, temp_dir):
    self.upload_video_dir = initTempDir(temp_dir, "upload_video")
    self.output_video_dir = initTempDir(temp_dir, "output_video")
    self.output_image_dir = initTempDir(temp_dir, "output_image")

  # TODO(Alex): This could be done on upload, something like this:
  # https://github.com/pallets/werkzeug/issues/1344#issuecomment-440589308
  def saveUploadToTemp(self, flask_file, name_prefix):
    extension = flask_file.content_type.split("/")
    if len(extension) == 2:
      extension = "." + extension[1]
    else:
      extension = "" # unknown filetype

    output_path = os.path.join(self.upload_video_dir, name_prefix + extension)
    flask_file.save(output_path, buffer_size=16384)
    flask_file.close()
    return output_path

  # example: https://gist.github.com/hiwonjoon/035a1ead72a767add4b87afe03d0dd7b
  @functools.lru_cache(maxsize=None)
  def info(self, file_path):
    args = [
      "ffprobe",
      "-hide_banner",
      "-v", "error",
      "-show_entries", "stream=width,height,duration",
      "-of", "default=noprint_wrappers=1:nokey=1",
      "-select_streams", "V",
      file_path
    ]

    out = subprocess.check_output(args) # shell=true will cause the cmd to fail.
    out = out.decode("utf-8").split("\n")
    return {"width": int(out[0]),
            "height": int(out[1]),
            "duration": float(out[2])}


  def encodeMP4(self, file_path, output_name, crf=23):
    output_path = os.path.join(self.output_video_dir, output_name)
    args = [
      "ffmpeg",
      "-hide_banner", "-y",
      "-i", file_path,
      "-c:v", "libx264",
      "-profile:v", "high", "-level", "4.0",
      "-crf", str(crf), # Default
      "-movflags", "+faststart",
      "-preset", "slower",
      "-pix_fmt", "yuv420p", # "Encoding for dumb players"
      output_path
    ]
    subprocess.check_call(args)
    return output_path

  def captureStill(self, file_path, output_name, start_time):
    output_path = os.path.join(self.output_image_dir, output_name)
    args = [
      "ffmpeg",
      "-hide_banner", "-y",
      "-ss", str(start_time),
      "-i", file_path,
      "-vframes", "1",
      "-f", "image2",
      output_path
    ]
    subprocess.check_call(args)
    return output_path

  def resizeImage(self, file_path, output_name, width=200):
    output_path = os.path.join(self.output_image_dir, output_name)
    with Image.open(file_path) as img:
      height = int(float(img.size[1]) * (width / float(img.size[0])))
      img.thumbnail((width, height), Image.ANTIALIAS)
      img.save(output_path)



