import os
import json

from dynaconf import FlaskDynaconf
from sqlalchemy.exc import DatabaseError
from flask import Flask, request
from flask_cors import CORS
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow

import api.models as models
from api.models import bcrypt
import api.routes as routes
import api.resources as resources


def create_app(name=__name__):
  app = Flask(name)
  FlaskDynaconf(app) # Initialize config

  app.config['JWT_BLACKLIST_ENABLED'] = True
  app.config['JWT_BLACKLIST_TOKEN_CHECKS'] = ['refresh']

  app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://{}:{}@{}/{}".format(
    app.config['DB_USER'],
    app.config['DB_PASSWORD'],
    app.config['DB_HOST'],
    app.config['DB_NAME'])

  app.logger.info('App configured to talk to DB: %s', app.config['SQLALCHEMY_DATABASE_URI'])

  cors = CORS(app, resources={r"/api/*": {"origins": app.config['ALLOWED_ORIGINS']}})
  models.db.init_app(app) # This needs to come before Marshmallow
  models.BaseModel.set_session(models.db.session)
  app.db = models.db
  migrate = Migrate(app, models.db)
  ma = Marshmallow(app)
  routes.api.init_app(app)
  resources.jwt.init_app(app)
  bcrypt.init_app(app)

  @app.route('/healthcheck')
  def healthcheck():
    return 'ok'

  @app.shell_context_processor
  def make_shell_context():
    """
     Adds these to the global scope of the shell for more convenient prototyping/debugging in the shell
     """
    from api.utils import module_classes_as_dict

    return {'db': models.db,
            **module_classes_as_dict('api.models'),
            **module_classes_as_dict('api.schemas'),
            **module_classes_as_dict('api.tests.factories')}

  return app
