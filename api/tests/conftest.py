import uuid
import pytest
from unittest.mock import PropertyMock

from api.app import create_app
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

@pytest.fixture(scope='session')
def db(app, request):
  return app.db

@pytest.fixture(scope='function')
def session(db, request):
  connection = db.engine.connect()
  transaction = connection.begin()

  options = dict(bind=connection, binds={})
  session = db.create_scoped_session(options=options)
  db.session = session

  BaseModel.set_session(session)

  def teardown():
    transaction.rollback()
    connection.close()
    session.remove()

  request.addfinalizer(teardown)
  return session

@pytest.fixture
def user():
  return f.UserFactory().save()

@pytest.fixture
def access_token(user):
  return user.create_access_token_with_claims()

@pytest.fixture(autouse=True)
def mock_storage(mocker):
  _storage = mocker.patch('api.models.storage')
  type(_storage.Client.return_value.get_bucket.return_value.blob.return_value).public_url = PropertyMock(return_value=str(uuid.uuid4()))
