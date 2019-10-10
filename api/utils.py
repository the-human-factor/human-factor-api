from dynaconf import settings
from importlib import import_module


def module_classes_as_dict(module_name):
  module = import_module(module_name)
  return dict(
    [
      (name, klass)
      for name, klass in module.__dict__.items()
      if isinstance(klass, type)
    ]
  )


def get_extension_from_content_type(f):
  content_type = f.content_type.split("/")
  if len(content_type) == 2:
    return content_type[1]
  return ""  # unknown filetype


def get_redis_url():
  if settings.get("REDIS_PASSWORD"):
    return "redis://:{}@{}:{}/{}".format(
      settings.get("REDIS_PASSWORD"),
      settings.get("REDIS_HOST"),
      settings.get("REDIS_PORT"),
      settings.get("REDIS_DB"),
    )
  else:
    return "redis://{}:{}/{}".format(
      settings.get("REDIS_HOST"), settings.get("REDIS_PORT"), settings.get("REDIS_DB")
    )
