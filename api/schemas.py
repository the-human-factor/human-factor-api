from marshmallow import fields
from flask_marshmallow.sqla import ModelSchema, HyperlinkRelated
import api.models as models


class VideoSchema(ModelSchema):
  class Meta:
    model = models.Video
    exclude = ('response', 'challenges')

class UserSchema(ModelSchema):
  class Meta:
    model = models.User
    exclude = ('challenges',)

class ChallengeSchema(ModelSchema):
  class Meta:
    model = models.Challenge

  video = fields.Nested(VideoSchema)
  user = fields.Nested(UserSchema)

class ResponseSchema(ModelSchema):
  class Meta:
    model = models.Response

  class ChallengeWithoutResponses(ChallengeSchema):
    class Meta:
      model = models.Challenge
      exclude = ('responses',) # Prevent circular serialization

  challenge = fields.Nested(ChallengeWithoutResponses)
  video = fields.Nested(VideoSchema)
  user = fields.Nested(UserSchema)
