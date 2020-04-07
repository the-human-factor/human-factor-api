from marshmallow import fields
from flask_marshmallow.sqla import ModelSchema

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


class ResponseWithoutChallenges(ModelSchema):
  class Meta:
    model = models.Response
    exclude = ["challenges"]  # Prevent circular serialization
    sqla_session = db.session

  video = fields.Nested(VideoSchema)
  user = fields.Nested(UserSchema)


class ChallengeSchema(ModelSchema):
  class Meta:
    model = models.Challenge
    exclude = ["responses"]
    sqla_session = db.session

  video = fields.Nested(VideoSchema)
  user = fields.Nested(UserSchema)
  responses = fields.Nested(ResponseWithoutChallenges, many=True)


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
