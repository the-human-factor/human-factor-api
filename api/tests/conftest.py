import uuid
import pytest
from unittest.mock import PropertyMock

from api.app import create_app, db
from api.models import BaseModel
import api.tests.factories as f


@pytest.fixture(scope='session')
def app(request):
  app = create_app(__name__)
  ctx = app.app_context()
  ctx.push()

  def teardown():
    ctx.pop()

  request.addfinalizer(teardown)
  return app

@pytest.fixture(autouse=True, scope='function')
def session(app, request):
  # No committing during tests
  db.session.commit = db.session.flush

  def teardown():
    db.session.rollback()

  request.addfinalizer(teardown)
  return db.session

@pytest.fixture(scope='function')
def user():
  return f.UserFactory(password='hunter2').save()

@pytest.fixture(scope='function')
def access_token(user):
  return user.create_access_token_with_claims()

@pytest.fixture(scope='function')
def refresh_token(user):
  return user.create_refresh_token()

@pytest.fixture(scope='function')
def video():
  return f.VideoFactory.create().save()

@pytest.fixture(scope='function')
def challenge():
  return f.ChallengeFactory.create().save()

@pytest.fixture(scope='function')
def response():
  return f.ResponseFactory.create().save()

@pytest.fixture(autouse=True)
def mock_storage(mocker):
  _storage = mocker.patch('api.models.storage')
  type(_storage.Client.return_value.get_bucket.return_value.blob.return_value).public_url = PropertyMock(return_value=str(uuid.uuid4()))
