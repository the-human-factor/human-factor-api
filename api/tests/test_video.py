import io
from flask import url_for
import api.tests.factories as f
import api.models as m

def test_create_video(client, access_token, video_blob):
  resp = client.post(url_for('createvideo'), buffered=True,
                     follow_redirects=True, content_type='multipart/form-data',
                     data=dict(videoBlob=(video_blob,'test.webm')),
                     headers={'Authorization': f"Bearer {access_token}"})

  assert resp.status_code == 201

def test_get_video(client, access_token):
  video = f.VideoFactory.create().save()

  resp = client.get(url_for('video', video_id=video.id),
                    headers={'Authorization': f"Bearer {access_token}"})

  assert resp.status_code == 200
  assert resp.json['id'] == str(video.id)

def test_get_video_without_token(client):
  video = f.VideoFactory.create().save()

  resp = client.get(url_for('video', video_id=video.id))

  assert resp.status_code == 401

def test_ingest_source_from_bucket():
  video = m.Video.create(url="test.webm")
  video.ingest_source_from_bucket()
  assert video.source_width == 640
  assert video.source_height == 480
  assert video.source_duration_sec == 4.186
