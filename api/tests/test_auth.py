from flask import url_for
import api.tests.factories as f

def test_user_registration(client, session):
  """Can register a new user"""
  resp = client.post(url_for('userregister'),
                       json=dict(
                         full_name='Cool Person',
                         email='coolperson@example.com',
                         password='hunter2'))

  assert resp.status_code == 201

  # Cannot register more than once with the same email
  resp = client.post(url_for('userregister'),
                       json=dict(
                         full_name='Cool Person',
                         email='coolperson@example.com',
                         password='hunter2'))

  assert resp.status_code == 409

def test_user_login(client, user):
  resp = client.post(url_for('userlogin'),
                       json=dict(
                         email=user.email,
                         password='hunter2'))

  assert resp.status_code == 200
  assert resp.json['user']['full_name'] == user.full_name
  assert resp.json['access_token'] != None
  assert resp.json['refresh_token'] != None

def test_wrong_password_login(client, user):
  resp = client.post(url_for('userlogin'),
                       json=dict(
                         email=user.email,
                         password='invalid-password'))

  assert resp.status_code == 401

def test_refresh_token(client, refresh_token):
  resp = client.post(url_for('userrefresh'),
                       headers={'Authorization': f"Bearer {refresh_token}"})

  assert resp.status_code == 200
  assert resp.json['access_token'] != None

def test_refresh_token_missing(client, refresh_token):
  resp = client.post(url_for('userrefresh'))

  assert resp.status_code == 401
