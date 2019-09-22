import io
import uuid

from flask import url_for
import api.tests.factories as f
import api.models as m


def test_create_response(client, access_token, response):
  resp = client.post(
    url_for("createresponse"),
    data=dict(
      challengeId=response.challenge.id,
      videoBlob=(io.BytesIO(b"fake video data"), "video.webm"),
    ),
    headers={"Authorization": f"Bearer {access_token}"},
  )

  assert resp.status_code == 201


def test_create_response_invalid_challenge(client, access_token, video_blob):
  resp = client.post(
    url_for("createresponse"),
    data=dict(challengeId=uuid.uuid4(), videoBlob=(video_blob, "video.webm")),
    headers={"Authorization": f"Bearer {access_token}"},
  )

  assert resp.status_code == 404


def test_list_responses(client, session, access_token):
  original_count = m.Response.query.count()
  responses = f.ResponseFactory.create_batch(size=10)

  resp = client.get(
    url_for("responselist"), headers={"Authorization": f"Bearer {access_token}"}
  )

  assert resp.status_code == 200
  assert len(resp.json) - original_count == 10

  # check that the responses have the all the fields we expect
  first = resp.json[0]
  assert first["challenge"] != None
  assert first["user"] != None
  assert first["video"] != None
