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
  content_type = f.content_type.replace(";", "/").split("/")
  if len(content_type) == 3 or len(content_type) == 2:
    return content_type[1]
  return ""  # unknown filetype


def get_redis_url(config):
  if config.get("REDIS_PASSWORD"):
    return "redis://:{}@{}:{}/{}".format(
      config.get("REDIS_PASSWORD"),
      config.get("REDIS_HOST"),
      config.get("REDIS_PORT"),
      config.get("REDIS_DB"),
    )
  else:
    return "redis://{}:{}/{}".format(
      config.get("REDIS_HOST"), config.get("REDIS_PORT"), config.get("REDIS_DB")
    )
