import sys
import uuid
import logging
import structlog

from dynaconf import FlaskDynaconf
from flask import Flask
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from flask_marshmallow import Marshmallow
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy as _BaseSQLAlchemy
from sqlalchemy.exc import DatabaseError
from sqlalchemy_mixins import AllFeaturesMixin

import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.redis import RedisIntegration


class SQLAlchemy(_BaseSQLAlchemy):
  def apply_pool_defaults(self, app, options):
    super(SQLAlchemy, self).apply_pool_defaults(app, options)
    options["pool_pre_ping"] = True


db = SQLAlchemy()
bcrypt = Bcrypt()
logger = structlog.get_logger()


class BaseModel(db.Model, AllFeaturesMixin):
  __abstract__ = True
  pass


def create_app(name=__name__):
  import api.routes as routes
  import api.resources as resources
  from api.jobs import celery

  app = Flask(name)
  FlaskDynaconf(app, ENVVAR_PREFIX_FOR_DYNACONF="FLASK")  # Initialize config
  config_logging(app)
  config_sentry(app)
  config_db(app)
  config_redis(app)

  CORS(app, resources={r"/api/*": {"origins": app.config["ALLOWED_ORIGINS"]}})

  db.init_app(app)  # This needs to come before Marshmallow
  BaseModel.set_session(db.session)
  Migrate(app, db)
  Marshmallow(app)
  routes.api.init_app(app)
  resources.jwt.init_app(app)
  bcrypt.init_app(app)
  celery.conf.update(app.config)

  @app.before_request
  def set_request_id():
    logger.new(request_id=str(uuid.uuid4()))

  @app.route("/healthcheck")
  def healthcheck():
    return "ok"

  @app.route("/version")
  def version():
    return app.config["GIT_COMMIT_SHA"]

  @app.route("/encode_a")
  def encode_a():
    from api.jobs import ingest_local_video2

    ingest_local_video2.queue("async")
    return "ok", 201

  @app.route("/encode_c")
  def encode_c():
    from api.jobs import ingest_local_video2

    ingest_local_video2.delay("celery")
    return "ok", 201

  @app.route("/encode")
  def encode():
    from api.jobs import ingest_local_video2

    ingest_local_video2("sync")
    return "ok", 201

  @app.shell_context_processor
  def make_shell_context():
    """
     Adds these to the global scope of the shell for more convenient prototyping/debugging in the shell
     """
    from api.utils import module_classes_as_dict

    return {
      "db": db,
      **module_classes_as_dict("api.models"),
      **module_classes_as_dict("api.schemas"),
      **module_classes_as_dict("api.tests.factories"),
    }

  @app.after_request
  def session_commit(res):
    res.headers["X-HF-git-commit-sha"] = app.config["GIT_COMMIT_SHA"]
    if res.status_code >= 400:
      return res
    try:
      db.session.commit()
      return res
    except DatabaseError:
      db.session.rollback()
      raise

  return app


def config_logging(app):
  logging.basicConfig(
    format="%(message)s", stream=sys.stdout, level=logging.INFO
  )  # TODO make level configurable

  processors = [
    structlog.processors.KeyValueRenderer(key_order=["event", "request_id"])
  ]

  structlog.configure(
    processors=processors,
    context_class=structlog.threadlocal.wrap_dict(dict),
    logger_factory=structlog.stdlib.LoggerFactory(),
  )


def config_db(app):
  app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://{}:{}@{}/{}".format(
    app.config["DB_USER"],
    app.config["DB_PASSWORD"],
    app.config["DB_HOST"],
    app.config["DB_NAME"],
  )

  logger.info(
    "App configured to talk to DB",
    db_uri="postgresql://{}:*REDACTED*@{}/{}".format(
      app.config["DB_USER"], app.config["DB_HOST"], app.config["DB_NAME"]
    ),
  )


def config_redis(app):
  from api.utils import get_redis_url

  redis_url = get_redis_url(app.config)

  logger.info("App configured to talk to Redis", redis_url=redis_url)


def config_sentry(app):
  sentry_sdk.init(
    app.config["SENTRY_DSN"],
    integrations=[
      FlaskIntegration(transaction_style="url"),
      CeleryIntegration(),
      SqlalchemyIntegration(),
      RedisIntegration(),
    ],
    environment=app.config["ENV"],
    release=f"human-factor-api@{app.config['GIT_COMMIT_SHA']}",
  )
