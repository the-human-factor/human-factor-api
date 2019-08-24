import io
import uuid

from flask import url_for
import api.tests.factories as f

def test_create_response(client, access_token, response):
  resp = client.post(url_for('createresponse'),
                     data=dict(
                       challenge_id=response.challenge.id,
                       video_blob=(io.BytesIO(b'fake video data'),'video.webm')),
                     headers={'Authorization': f"Bearer {access_token}"})

  assert resp.status_code == 201

def test_create_response_invalid_challenge(client, access_token):
  resp = client.post(url_for('createresponse'),
                     data=dict(
                       challenge_id=uuid.uuid4(),
                       video_blob=(io.BytesIO(b'fake video data'),'video.webm')),
                     headers={'Authorization': f"Bearer {access_token}"})

  assert resp.status_code == 404

def test_list_responses(client, session, access_token):
  responses = f.ResponseFactory.create_batch(size=10)

  resp = client.get(url_for('responselist'),
                    headers={'Authorization': f"Bearer {access_token}"})

  assert resp.status_code == 200
  assert len(resp.json) == 10
