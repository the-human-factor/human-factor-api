import os
import subprocess
import tempfile
import functools
import shutil
from PIL import Image

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

# FFMPEF H.264 settings:
# https://trac.ffmpeg.org/wiki/Encode/H.264
def encode_mp4(self, file_path, output_name, crf="23", speed="slower"):
  output_path = os.path.join(self.output_video_dir, output_name)
  args = [
    "ffmpeg",
    "-hide_banner", "-y",
    "-i", file_path,
    "-c:v", "libx264",
    "-crf", crf,
    "-preset", speed,
    "-pix_fmt", "yuv420p", # "Encoding for dumb players"
    "-profile:v", "high", "-level", "4.0", # Compatibility flags
    "-movflags", "+faststart",
    output_path
  ]
  subprocess.check_call(args)
  return output_path

def capture_still(self, file_path, output_name, start_time):
  output_path = os.path.join(self.output_image_dir, output_name)
  args = [
    "ffmpeg",
    "-hide_banner", "-y",
    "-ss", str(start_time), # start time is in seconds
    "-i", file_path,
    "-vframes", "1",
    "-f", "image2",
    output_path
  ]
  subprocess.check_call(args)
  return output_path

def resize_image(self, input_path, output_path, width=200):
  with Image.open(input_path) as img:
    height = int(float(img.size[1]) * (width / float(img.size[0])))
    img.thumbnail((width, height), Image.ANTIALIAS)
    img.save(output_path)
