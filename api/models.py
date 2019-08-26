from datetime import datetime

from flask import current_app
from flask_sqlalchemy import SQLAlchemy, Model
from google.cloud import storage
from flask_sqlalchemy import SQLAlchemy, Model
from flask_jwt_extended import create_access_token, create_refresh_token

import sqlalchemy
from sqlalchemy.exc import DatabaseError
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import backref
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID

from api.app import db, bcrypt, BaseModel

class Video(BaseModel):
  __tablename__ = 'videos'

  id = db.Column(UUID(as_uuid=True), server_default=sqlalchemy.text("gen_random_uuid()"), primary_key=True)

  url = db.Column(db.String(512))

  created_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), nullable=False)
  updated_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), onupdate=datetime.utcnow, nullable=False)

  @staticmethod
  def create_and_upload(file):
    video = Video.create()
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(current_app.config['VIDEO_BUCKET'])
    blob = bucket.blob("{}.webm".format(video.id))

    blob.upload_from_file(file.stream, predefined_acl="publicRead")

    video.update(url=blob.public_url)

    return video


class Challenge(BaseModel):
  __tablename__ = 'challenges'

  id = db.Column(UUID(as_uuid=True), server_default=sqlalchemy.text("gen_random_uuid()"), primary_key=True)

  title = db.Column(db.Unicode(length=255), nullable=False)
  instructions = db.Column(db.UnicodeText, nullable=False)
  grading_notes = db.Column(db.UnicodeText, nullable=False)

  user = db.relationship('User', backref='challenges')
  user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'))

  video = db.relationship('Video', backref=backref('challenges', uselist=False))
  video_id = db.Column(UUID(as_uuid=True), db.ForeignKey('videos.id'), nullable=True)

  created_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), nullable=False)
  updated_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), onupdate=datetime.utcnow, nullable=False)


class User(BaseModel):
  __tablename__ = 'users'

  id = db.Column(UUID(as_uuid=True), server_default=sqlalchemy.text("gen_random_uuid()"), primary_key=True)
  full_name = db.Column(db.Unicode(255))
  email = db.Column(db.String(255), unique=True, nullable=False)
  _password = db.Column('password', db.String(255), nullable=False)

  created_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), nullable=False)
  updated_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), onupdate=datetime.utcnow, nullable=False)

  @hybrid_property
  def password(self):
    return self._password

  @password.setter
  def password(self, password):
    self._password = bcrypt.generate_password_hash(password).decode()

  def check_password(self, password):
    return bcrypt.check_password_hash(self.password, password)

  def create_access_token_with_claims(self):
    # TODO: Implement claims
    claims = {'roles': [{'admin': 'admin'},]}
    return create_access_token(identity=self.id, user_claims=claims)

  def create_refresh_token(self):
    return create_refresh_token(identity=self.id)

class BlacklistedToken(BaseModel):
  __tablename__ = 'blacklisted_tokens'

  jti = db.Column(db.String(64), primary_key=True)
  exp = db.Column(db.DateTime(timezone=True), nullable=False)


class Response(BaseModel):
  __tablename__ = 'responses'

  id = db.Column(UUID(as_uuid=True), server_default=sqlalchemy.text("gen_random_uuid()"), primary_key=True)

  challenge = db.relationship('Challenge', backref='responses')
  challenge_id = db.Column(UUID(as_uuid=True), db.ForeignKey('challenges.id'), primary_key=True)

  user = db.relationship('User', backref='responses')
  user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), primary_key=True)

  video = db.relationship('Video', backref=backref('response', uselist=False))
  video_id = db.Column(UUID(as_uuid=True), db.ForeignKey('videos.id'), nullable=True)

  created_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), nullable=False)
  updated_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), onupdate=datetime.utcnow, nullable=False)
