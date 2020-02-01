import io
import uuid

from flask import url_for
import api.tests.factories as f
import api.models as m


def test_create_sequence(client, access_token):
  resp = client.post(
    url_for("createsequence"),
    data=dict(title="empty sequence", itemsJson="[]"),
    headers={"Authorization": f"Bearer {access_token}"},
  )

  print(resp)
  assert resp.status_code == 201


def test_create_sequence_invalid_json(client, access_token):
  resp = client.post(
    url_for("createresponse"),
    data=dict(title="broken json sequence", itemsJson="["),
    headers={"Authorization": f"Bearer {access_token}"},
  )

  assert resp.status_code == 400


# test
# with different numbers of videos and challenges
# loop through
# challenge,video > [(2,0), (2,1), (1,2), (2,0), (0,0)]
# generate_simple_json


def test_list_responses(client, user, session, access_token, admin_access_token):
  original_count = m.Sequence.query.count()

  variations = [(2, 0), (2, 1), (1, 2), (2, 0), (0, 0)]

  challenges = f.ChallengeFactory.create_batch(size=2)
  videos = f.VideoFactory.create_batch(size=2)

  sequences = []

  for challenge_count, video_count in variations:
    sequences.append(
      f.SequenceFactory.create(
        challenges=challenges[:challenge_count], videos=videos[:video_count]
      )
    )

  resp = client.get(
    url_for("sequencelist"), headers={"Authorization": f"Bearer {admin_access_token}"}
  )

  assert resp.status_code == 200
  assert len(resp.json) - original_count == len(variations)

  # check that the responses have the all the fields we expect
  first = resp.json[0]
  assert first["challenges"] != None
  assert first["videos"] == None
