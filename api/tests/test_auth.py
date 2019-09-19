from flask import url_for

import api.models as m
import api.tests.factories as f

def test_user_registration(client):
  """Can register a new user"""
  resp = client.post(url_for('userregister'),
                       json=dict(
                         fullName='Cool Person',
                         email='coolperson@example.com',
                         password='hunter2'))

  assert resp.status_code == 201

  # Cannot register more than once with the same email
  resp = client.post(url_for('userregister'),
                       json=dict(
                         fullName='Cool Person',
                         email='coolperson@example.com',
                         password='hunter2'))

  assert resp.status_code == 409

def test_user_registration_missing_keys(client):
  """Missing keys during registration causes a 400"""

  resp = client.post(url_for('userregister'),
                       json=dict(
                         email='coolperson@example.com',
                         password='hunter2'))

  assert resp.status_code == 400

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

def test_missing_fields_login(client, user):
  resp = client.post(url_for('userlogin'),
                     json={})

  assert resp.status_code == 400

def test_refresh_token(client, refresh_token):
  resp = client.post(url_for('userrefresh'),
                       headers={'Authorization': f"Bearer {refresh_token}"})

  assert resp.status_code == 200
  assert resp.json['access_token'] != None

def test_refresh_token_missing(client, refresh_token):
  resp = client.post(url_for('userrefresh'))

  assert resp.status_code == 401

def test_change_password_success(client, access_token):
  new_password = 'Test123123'
  resp = client.put(url_for('userpassword'),
                    json=dict(
                      oldPassword='hunter2',
                      password=new_password),
                    headers={'Authorization': f"Bearer {access_token}"})

  assert resp.status_code == 200
  assert resp.json['access_token'] != None
  assert resp.json['refresh_token'] != None

  user = m.User.where(email='test-user@example.com').one_or_none()
  assert user.check_password(new_password) == True

def test_change_password_failure(client, access_token):
  resp = client.put(url_for('userpassword'),
                    json=dict(
                      oldPassword='hunter3', # wrong pass
                      password='Test123123'),
                    headers={'Authorization': f"Bearer {access_token}"})

  assert resp.status_code == 400

  user = m.User.where(email='test-user@example.com').one_or_none()
  assert user.check_password('hunter2') == True # old password
