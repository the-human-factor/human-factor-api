import os
import structlog

from datetime import datetime, timedelta
from dynaconf import settings

from flask import current_app
from flask_jwt_extended import create_access_token, create_refresh_token
from google.cloud import storage
from tempfile import TemporaryDirectory

import sqlalchemy
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import backref, relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID

from api.app import db, bcrypt, BaseModel
from api import ffmpeg
from api.utils import get_extension_from_content_type
from api.jobs import ingest_video

log = structlog.get_logger()

BUFFER_SIZE = 2 ** 14  # 16KiB


class Video(BaseModel):
  __tablename__ = "videos"

  id = db.Column(
    UUID(as_uuid=True),
    server_default=sqlalchemy.text("gen_random_uuid()"),
    primary_key=True,
  )

  url = db.Column(db.String(512))
  source_url = db.Column(db.String(512))
  still_url = db.Column(db.String(512))
  thumbnail_url = db.Column(db.String(512))

  source_width = db.Column(db.Integer())
  source_height = db.Column(db.Integer())
  source_duration_sec = db.Column(db.Float())

  encoded_at = db.Column(db.DateTime(timezone=True), nullable=True)
  created_at = db.Column(
    db.DateTime(timezone=True), server_default=func.now(), nullable=False
  )
  updated_at = db.Column(
    db.DateTime(timezone=True),
    server_default=func.now(),
    onupdate=datetime.utcnow,
    nullable=False,
  )

  @property
  def source_url_blob_name(self):
    return self.url.split("/")[-1]

  @staticmethod
  def create_and_upload(file):
    video = Video.create()

    extension = get_extension_from_content_type(file)
    source_name = "{}.{}".format(video.id, extension)

    with TemporaryDirectory(prefix="upload_video") as temp_dir:
      path = os.path.join(temp_dir, source_name)
      file.save(path, buffer_size=BUFFER_SIZE)  # TODO: make constant

      storage_client = storage.Client()
      bucket = storage_client.get_bucket(current_app.config["STATIC_BUCKET"])
      blob = bucket.blob(current_app.config["BUCKET_SOURCE_PREFIX"] + source_name)

      blob.upload_from_filename(
        path, content_type=file.content_type, predefined_acl="publicRead"
      )

    video.update(url=blob.public_url, source_url=blob.public_url)

    # Enqueue
    ingest_video.delay(video.id)

    return video

  def ingest_source_from_bucket(self):
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(current_app.config["STATIC_BUCKET"])

    with TemporaryDirectory(prefix="media") as temp_dir:
      source_name = self.source_url_blob_name
      source_video_path = os.path.join(temp_dir, source_name)
      blob = bucket.blob(current_app.config["BUCKET_SOURCE_PREFIX"] + source_name)

      blob.download_to_filename(source_video_path)

      self.ingest_local_source(temp_dir, source_video_path)

  def ingest_local_source(self, temp_dir, source_video_name):
    config = current_app.config
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(config["STATIC_BUCKET"])

    reencoded_name = "{}.mp4".format(self.id)
    still_name = "{}.jpg".format(self.id)
    output_thumbnail_name = "{}_thumb.jpg".format(self.id)

    source_path = os.path.join(temp_dir, source_video_name)
    reencoded_path = os.path.join(temp_dir, reencoded_name)
    still_path = os.path.join(temp_dir, still_name)
    thumbnail_path = os.path.join(temp_dir, output_thumbnail_name)

    log.info("enc: ncoding video", source_path)
    ffmpeg.encode_mp4(
      source_path,
      reencoded_path,
      crf=config["FFMPEG_DEFAULT_CRF"],
      speed=config["FFMPEG_DEFAULT_SPEED"],
    )

    video_stats = ffmpeg.info(reencoded_path)
    log.info("enc: encoding video", reencoded_path)

    ffmpeg.capture_still(
      reencoded_path, still_path, at_time=video_stats["duration"] / 1.8
    )

    ffmpeg.resize_image(
      still_path, thumbnail_path, width=config["STILL_THUMBNAIL_WIDTH"]
    )

    reencoded_blob = bucket.blob(config["BUCKET_VIDEO_PREFIX"] + reencoded_name)
    still_blob = bucket.blob(config["BUCKET_STILL_PREFIX"] + still_name)
    thumbnail_blob = bucket.blob(config["BUCKET_THUMB_PREFIX"] + still_name)

    log.info("enc: uploading blobs", reencoded_blob, still_blob, thumbnail_blob)

    reencoded_blob.upload_from_filename(
      reencoded_path, content_type="video/mp4", predefined_acl="publicRead"
    )

    still_blob.upload_from_filename(
      still_path, content_type="image/jpeg", predefined_acl="publicRead"
    )

    thumbnail_blob.upload_from_filename(
      thumbnail_path, content_type="image/jpeg", predefined_acl="publicRead"
    )

    log.info("enc: updating postgres")

    self.update(
      url=reencoded_blob.public_url,
      still_url=still_blob.public_url,
      thumbnail_url=thumbnail_blob.public_url,
      source_width=video_stats["width"],
      source_height=video_stats["height"],
      source_duration_sec=video_stats["duration"],
      encoded_at=datetime.utcnow(),
    )


class Challenge(BaseModel):
  __tablename__ = "challenges"
  __table_args__ = (db.Index("challenges_by_user_id_listed", "user_id", "listed"),)

  id = db.Column(
    UUID(as_uuid=True),
    server_default=sqlalchemy.text("gen_random_uuid()"),
    primary_key=True,
  )

  title = db.Column(db.Unicode(length=255), nullable=False)
  instructions = db.Column(db.UnicodeText, nullable=False)
  grading_notes = db.Column(db.UnicodeText, nullable=False)
  listed = db.Column(db.Boolean, default=False, nullable=False, index=True)

  user = db.relationship("User", backref="challenges")
  user_id = db.Column(UUID(as_uuid=True), db.ForeignKey("users.id"))

  video = db.relationship("Video", backref=backref("challenges", uselist=False))
  video_id = db.Column(UUID(as_uuid=True), db.ForeignKey("videos.id"), nullable=True)

  deleted_at = db.Column(db.DateTime(timezone=True), nullable=True)
  created_at = db.Column(
    db.DateTime(timezone=True), server_default=func.now(), nullable=False
  )
  updated_at = db.Column(
    db.DateTime(timezone=True),
    server_default=func.now(),
    onupdate=datetime.utcnow,
    nullable=False,
  )


class Role(BaseModel):
  __tablename__ = "roles"

  id = db.Column(db.String(255), primary_key=True)

  def __repr__(self):
    return f"<Role {self.id}>"

  @staticmethod
  def of(id):
    return Role.where(id=id).one_or_none()


class User(BaseModel):
  __tablename__ = "users"

  id = db.Column(
    UUID(as_uuid=True),
    server_default=sqlalchemy.text("gen_random_uuid()"),
    primary_key=True,
  )
  full_name = db.Column(db.Unicode(255), nullable=False)
  email = db.Column(db.String(255), unique=True, nullable=False)
  _password = db.Column("password", db.String(255), nullable=False)

  role = db.Column(
    db.String(255),
    db.ForeignKey("roles.id", name="fk_user_role"),
    default="user",
    nullable=False,
  )

  created_at = db.Column(
    db.DateTime(timezone=True), server_default=func.now(), nullable=False
  )
  updated_at = db.Column(
    db.DateTime(timezone=True),
    server_default=func.now(),
    onupdate=datetime.utcnow,
    nullable=False,
  )

  @hybrid_property
  def password(self):
    return self._password

  @password.setter
  def password(self, password):
    self._password = bcrypt.generate_password_hash(password).decode()

  def check_password(self, password):
    return bcrypt.check_password_hash(self.password, password)

  def create_access_token_with_claims(
    self, expires_minutes=settings["JWT_EXPIRATION_MINUTES"]
  ):
    claims = {"role": self.role}
    return create_access_token(
      identity=self.id,
      user_claims=claims,
      expires_delta=timedelta(minutes=expires_minutes),
    )

  def create_refresh_token(
    self, expires_hours=settings["JWT_REFRESH_EXPIRATION_HOURS"]
  ):
    return create_refresh_token(
      identity=self.id, expires_delta=timedelta(hours=expires_hours)
    )

  @staticmethod
  def get_or_create_super_admin():
    user = User.where(email="super_admin@thehumanfactor.ai").one_or_none()
    if not user:
      user = User.create(
        full_name="Super Admin",
        email="super_admin@thehumanfactor.ai",
        password="iamsuperspecialforsure",
        role=Role.of("super_admin"),
      )

    return user

  def __repr__(self):
    return f"<User {self.email}>"


class BlacklistedToken(BaseModel):
  __tablename__ = "blacklisted_tokens"

  jti = db.Column(db.String(64), primary_key=True)
  exp = db.Column(db.DateTime(timezone=True), nullable=False)


sequence_response_response_association_table = db.Table(
  "sequence_response_response_association",
  BaseModel.metadata,
  db.Column(
    "sequence_responses_id", UUID(as_uuid=True), db.ForeignKey("sequence_responses.id")
  ),
  db.Column("response_id", UUID(as_uuid=True), db.ForeignKey("responses.id")),
)


class Response(BaseModel):
  __tablename__ = "responses"

  id = db.Column(
    UUID(as_uuid=True),
    server_default=sqlalchemy.text("gen_random_uuid()"),
    primary_key=True,
    unique=True,
  )

  challenge = db.relationship("Challenge", backref="responses")
  challenge_id = db.Column(
    UUID(as_uuid=True), db.ForeignKey("challenges.id"), primary_key=True
  )

  user = db.relationship("User", backref="responses")
  user_id = db.Column(UUID(as_uuid=True), db.ForeignKey("users.id"), primary_key=True)

  video = db.relationship("Video", backref=backref("response", uselist=False))
  video_id = db.Column(UUID(as_uuid=True), db.ForeignKey("videos.id"), nullable=True)

  hidden = db.Column(db.Boolean, default=False, nullable=False)

  sequence_responses = relationship(
    "SequenceResponse", secondary=sequence_response_response_association_table
  )

  created_at = db.Column(
    db.DateTime(timezone=True), server_default=func.now(), nullable=False
  )
  updated_at = db.Column(
    db.DateTime(timezone=True),
    server_default=func.now(),
    onupdate=datetime.utcnow,
    nullable=False,
  )


sequence_challenges_association_table = db.Table(
  "sequence_challenges_association",
  BaseModel.metadata,
  db.Column("sequence_id", UUID(as_uuid=True), db.ForeignKey("sequences.id")),
  db.Column("challenge_id", UUID(as_uuid=True), db.ForeignKey("challenges.id")),
)

sequence_videos_association_table = db.Table(
  "sequence_videos_association",
  BaseModel.metadata,
  db.Column("sequence_id", UUID(as_uuid=True), db.ForeignKey("sequences.id")),
  db.Column("video_id", UUID(as_uuid=True), db.ForeignKey("videos.id")),
)


class Sequence(BaseModel):
  __tablename__ = "sequences"

  id = db.Column(
    UUID(as_uuid=True),
    server_default=sqlalchemy.text("gen_random_uuid()"),
    primary_key=True,
  )

  title = db.Column(db.Unicode(length=255), nullable=False)
  items_json = db.Column(db.UnicodeText, nullable=False)
  items_length = db.Column(db.Integer, nullable=False)

  challenges = relationship(
    "Challenge", secondary=sequence_challenges_association_table
  )

  videos = relationship("Video", secondary=sequence_videos_association_table)

  created_at = db.Column(
    db.DateTime(timezone=True), server_default=func.now(), nullable=False
  )
  updated_at = db.Column(
    db.DateTime(timezone=True),
    server_default=func.now(),
    onupdate=datetime.utcnow,
    nullable=False,
  )


class SequenceResponse(BaseModel):
  __tablename__ = "sequence_responses"

  id = db.Column(
    UUID(as_uuid=True),
    server_default=sqlalchemy.text("gen_random_uuid()"),
    primary_key=True,
    unique=True,  # Needed to add this so that responses+ this fkey didn't error.
  )

  user = db.relationship("User", backref="sequence_responses")
  user_id = db.Column(UUID(as_uuid=True), db.ForeignKey("users.id"), primary_key=True)

  sequence = db.relationship("Sequence", backref="sequence_responses")
  sequence_id = db.Column(
    UUID(as_uuid=True), db.ForeignKey("sequences.id"), primary_key=True
  )

  responses = relationship(
    "Response", secondary=sequence_response_response_association_table
  )

  hide_responses = db.Column(db.Boolean, default=False, nullable=False)

  started_at = db.Column(db.DateTime(timezone=True), nullable=True)
  items_finished = db.Column(db.Integer, default=0, nullable=False)
  finished = db.Column(db.Boolean, default=False, nullable=False)

  created_at = db.Column(
    db.DateTime(timezone=True), server_default=func.now(), nullable=False
  )

  updated_at = db.Column(
    db.DateTime(timezone=True),
    server_default=func.now(),
    onupdate=datetime.utcnow,
    nullable=False,
  )
