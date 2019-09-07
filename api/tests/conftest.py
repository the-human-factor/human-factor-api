import os
import pytest
import shutil
import uuid
from unittest.mock import PropertyMock

from api.app import create_app, db
from api.models import BaseModel
import api.tests.factories as f
from werkzeug import FileStorage

TEST_WEBM_PATH = './api/tests/data/test.webm'

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
  return f.UserFactory(email='test-user@example.com', password='hunter2').save()

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

@pytest.fixture
def video_blob():
  return open(TEST_WEBM_PATH, "rb")

def save_video_into(file_path):
  shutil.copy(TEST_WEBM_PATH, file_path)

def check_file_exists(file_path, **kwargs):
  if os.path.getsize(file_path) == 0:
    raise ValueError("file is empty, {}".format(file_path))

@pytest.fixture(autouse=True)
def mock_storage(mocker):
  _storage = mocker.patch('api.models.storage')
  type(_storage.Client.return_value.get_bucket.return_value.blob.return_value).public_url = PropertyMock(return_value=str(uuid.uuid4()))
  _storage.Client().get_bucket().blob().download_to_filename.side_effect = save_video_into
  _storage.Client().get_bucket().blob().upload_from_filename.side_effect = check_file_exists

