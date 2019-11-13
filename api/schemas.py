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


class ChallengeSchemaWithoutResponses(ChallengeSchema):
  class Meta:
    model = models.Challenge
    exclude = ["responses"]  # Prevent circular serialization
    sqla_session = db.session


class ResponseSchema(ModelSchema):
  class Meta:
    model = models.Response
    sqla_session = db.session

  challenge = fields.Nested(ChallengeSchemaWithoutResponses)
  video = fields.Nested(VideoSchema)
  user = fields.Nested(UserSchema)


class SequenceResponseWithoutSequenceSchema(ModelSchema):
  class Meta:
    model = models.SequenceResponse
    exclude = ["sequence"]
    sqla_session = db.session

  responses = fields.List(fields.Nested(ResponseSchema))


class SequenceSchema(ModelSchema):
  class Meta:
    model = models.Sequence
    sqla_session = db.session

  challenges = fields.List(fields.Nested(ChallengeSchemaWithoutResponses))
  videos = fields.List(fields.Nested(VideoSchema))
  responses = fields.List(fields.Nested(SequenceResponseWithoutSequenceSchema))


class SequenceHiddenResponsesSchema(ModelSchema):
  class Meta:
    model = models.Sequence
    exclude = ["sequence_responses"]
    sqla_session = db.session

  challenges = fields.List(fields.Nested(ChallengeSchemaWithoutResponses))
  videos = fields.List(fields.Nested(VideoSchema))


class SequenceResponseSchema(ModelSchema):
  class Meta:
    model = models.SequenceResponse
    sqla_session = db.session

  sequence = fields.Nested(SequenceSchema)
  responses = fields.List(fields.Nested(ResponseSchema))


class SequenceResponseHiddenResponsesSchema(ModelSchema):
  class Meta:
    model = models.SequenceResponse
    exclude = ["responses"]
    sqla_session = db.session

  sequence = fields.Nested(SequenceHiddenResponsesSchema)
