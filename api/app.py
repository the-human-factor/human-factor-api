import os
import sys
import uuid
import json
import logging
import structlog

from dynaconf import FlaskDynaconf
from sqlalchemy.exc import DatabaseError
from flask import Flask, request
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from sqlalchemy_mixins import AllFeaturesMixin

import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

db = SQLAlchemy()
bcrypt = Bcrypt()
logger = structlog.get_logger()

class BaseModel(db.Model, AllFeaturesMixin):
  __abstract__ = True
  pass

def create_app(name=__name__):
  import api.routes as routes
  import api.resources as resources

  app = Flask(name)
  FlaskDynaconf(app) # Initialize config
  config_logging(app)

  sentry_sdk.init(
    app.config['SENTRY_DSN'],
    integrations=[FlaskIntegration(transaction_style="url")],
    environment=app.config['ENV'],
    release=f"human-factor-api@{app.config['GIT_COMMIT_SHA']}"
  )

  app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://{}:{}@{}/{}".format(
    app.config['DB_USER'],
    app.config['DB_PASSWORD'],
    app.config['DB_HOST'],
    app.config['DB_NAME'])

  app.logger.info('App configured to talk to DB: %s', "postgresql://{}:*REDACTED*@{}/{}".format(
    app.config['DB_USER'],
    app.config['DB_HOST'],
    app.config['DB_NAME']))

  cors = CORS(app, resources={
    r"/api/*": { "origins": app.config['ALLOWED_ORIGINS'] }
  })
  
  db.init_app(app) # This needs to come before Marshmallow
  BaseModel.set_session(db.session)
  migrate = Migrate(app, db)
  ma = Marshmallow(app)
  routes.api.init_app(app)
  resources.jwt.init_app(app)
  bcrypt.init_app(app)

  @app.before_request
  def set_request_id():
    logger.new(request_id=str(uuid.uuid4()))

  @app.route('/healthcheck')
  def healthcheck():
    return 'ok'

  @app.route('/version')
  def version():
    return app.config['GIT_COMMIT_SHA']

  @app.shell_context_processor
  def make_shell_context():
    """
     Adds these to the global scope of the shell for more convenient prototyping/debugging in the shell
     """
    from api.utils import module_classes_as_dict

    return {'db': db,
            **module_classes_as_dict('api.models'),
            **module_classes_as_dict('api.schemas'),
            **module_classes_as_dict('api.tests.factories')}

  @app.after_request
  def session_commit(res):
    res.headers["X-HF-git-commit-sha"] = app.config['GIT_COMMIT_SHA']
    if res.status_code >= 400:
      return res
    try:
      db.session.commit()
      return res
    except DatabaseError:
      db.session.rollback()
      raise

  @app.route('/debug-sentry')
  def trigger_error():
    division_by_zero = 1 / 0

  return app

def config_logging(app):
  logging.basicConfig(format="%(message)s", stream=sys.stdout, level=logging.INFO) # TODO make level configurable

  processors = [structlog.processors.KeyValueRenderer(key_order=["event", "request_id"])]

  structlog.configure(
    processors=processors,
    context_class=structlog.threadlocal.wrap_dict(dict),
    logger_factory=structlog.stdlib.LoggerFactory()
  )
