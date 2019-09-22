from marshmallow import fields
from flask_marshmallow.sqla import ModelSchema, HyperlinkRelated

import api.models as models
from api.app import db


class VideoSchema(ModelSchema):
  class Meta:
    model = models.Video
    exclude = ("response", "challenges")
    sqla_session = db.session


class UserSchema(ModelSchema):
  class Meta:
    model = models.User
    exclude = ["challenges", "_password", "email", "responses"]
    sqla_session = db.session


class ChallengeSchema(ModelSchema):
  class Meta:
    model = models.Challenge
    sqla_session = db.session

  video = fields.Nested(VideoSchema)
  user = fields.Nested(UserSchema)


class ResponseSchema(ModelSchema):
  class Meta:
    model = models.Response
    sqla_session = db.session

  class ChallengeWithoutResponses(ChallengeSchema):
    class Meta:
      model = models.Challenge
      exclude = ["responses"]  # Prevent circular serialization
      sqla_session = db.session

  challenge = fields.Nested(ChallengeWithoutResponses)
  video = fields.Nested(VideoSchema)
  user = fields.Nested(UserSchema)
