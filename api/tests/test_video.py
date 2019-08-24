import io
from flask import url_for
import api.tests.factories as f

def test_create_video(client, access_token):
  resp = client.post(url_for('createvideo'), buffered=True,
                     follow_redirects=True, content_type='multipart/form-data',
                     data=dict(video_blob=(io.BytesIO(b'fake video data'),'video.webm')),
                     headers={'Authorization': f"Bearer {access_token}"})

  assert resp.status_code == 201

def test_get_video(client, access_token):
  video = f.VideoFactory.create().save()

  resp = client.get(url_for('video', video_id=video.id),
                    headers={'Authorization': f"Bearer {access_token}"}
  )

  assert resp.status_code == 200
  assert resp.json['id'] == str(video.id)
