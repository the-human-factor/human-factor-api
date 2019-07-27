import io
from flask import url_for

import api.tests.factories as f
import api.models as m


def test_app(client):
  assert client.get('/healthcheck').status_code == 200

def test_create_video(client, access_token):


  data = {}
  data['video_blob'] = (io.BytesIO(b"abcdef"), 'test.jpg')

  resp = client.post(url_for('createvideo'), buffered=True,
                     follow_redirects=True, content_type='multipart/form-data',
                     data=dict(video_blob=(io.BytesIO(b'fake video data'),'video.webm')),
                     headers={'Authorization': f"Bearer {access_token}"}
  )

  assert resp.status_code == 201
