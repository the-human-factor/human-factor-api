import factory
import random
import api.models as m

from uuid import uuid4


class VideoFactory(factory.alchemy.SQLAlchemyModelFactory):
  class Meta:
    model = m.Video
    sqlalchemy_session = m.db.session

  url = factory.Faker("url")


class UserFactory(factory.alchemy.SQLAlchemyModelFactory):
  class Meta:
    model = m.User
    sqlalchemy_session = m.db.session

  full_name = factory.Faker("name")
  email = factory.Faker("email")
  password = factory.Faker("password")

  # Need lazyness here https://github.com/FactoryBoy/factory_boy/issues/445
  @factory.lazy_attribute
  def role(self):
    random.choice([role.id for role in m.Role.all()])


class ChallengeFactory(factory.alchemy.SQLAlchemyModelFactory):
  class Meta:
    model = m.Challenge
    sqlalchemy_session = m.db.session

  title = factory.Faker("name")
  instructions = factory.Faker("text")
  grading_notes = factory.Faker("text")

  user = factory.SubFactory(UserFactory)
  video = factory.SubFactory(VideoFactory)


class ResponseFactory(factory.alchemy.SQLAlchemyModelFactory):
  class Meta:
    model = m.Response
    sqlalchemy_session = m.db.session

  challenge = factory.SubFactory(ChallengeFactory)
  video = factory.SubFactory(VideoFactory)
  user = factory.SubFactory(UserFactory)


class ChallengeWithResponseFactory(ChallengeFactory):
  membership = factory.RelatedFactory(ResponseFactory, "challenge")


def create_sequence_json(challenges, videos):
  result = []
  i = 100
  for challenge in challenges:
    result.append({"id": i, "type": "challenge", "challenge_id": challenge.id})
    i += 1
  for video in videos:
    result.append({"id": i, "type": "video", "challenge_id": video.id})
    i += 1


class SequenceFactory(factory.alchemy.SQLAlchemyModelFactory):
  class Meta:
    model = m.Sequence
    sqlalchemy_session = m.db.session

  title = factory.Faker("name")
  items_json = "[]"
  items_length = 0

  # @factory.post_generation
  # def items_json(self, create, extracted, **kwargs):
  #   if not create:
  #     return  # Simple build, do nothing.

  #   print(kwargs)
  #   self.items_json = create_sequence_json(kwargs["challenges"], kwargs["videos"])
  #   self.items_length = len(kwargs["challenges"]) + len(kwargs["videos"])

  @factory.post_generation
  def challenges(self, create, extracted):
    if not create:
      return  # Simple build, do nothing.

    if extracted:
      for challenge in extracted:
        self.challeges.add(challenge)

    print("post_generation challenges")

  @factory.post_generation
  def videos(self, create, extracted):
    if not create:
      return  # Simple build, do nothing.

    if extracted:
      for video in extracted:
        self.videos.add(video)

    print("post_generation video")
    self.items_json = create_sequence_json(self.challenges, self.videos)
    self.items_length = len(self.challenges) + len(self.videos)
    print("created items_json")
