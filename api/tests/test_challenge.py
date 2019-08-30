import io
from flask import url_for
import api.tests.factories as f

def test_create_challenge(client, access_token):
  resp = client.post(url_for('createchallenge'),
                     data=dict(
                     title='Test Challenge',
                     instructions='Some Instructions',
                     gradingNotes='This is how it is done',
                     videoBlob=(io.BytesIO(b'fake video data'),'video.webm')),
                     headers={'Authorization': f"Bearer {access_token}"})

  assert resp.status_code == 201

def test_get_challenge(client, access_token):
  challenge = f.ChallengeFactory.create().save()

  resp = client.get(url_for('challenge', challenge_id=challenge.id),
                    headers={'Authorization': f"Bearer {access_token}"})

  assert resp.status_code == 200
  assert resp.json['id'] == str(challenge.id)

def test_list_challenges(client, session, access_token):
  challenges = f.ChallengeFactory.create_batch(size=10)
  session.add_all(challenges)
  session.commit()

  resp = client.get(url_for('challengelist'),
                    headers={'Authorization': f"Bearer {access_token}"})

  assert resp.status_code == 200
  assert len(resp.json) == 10
