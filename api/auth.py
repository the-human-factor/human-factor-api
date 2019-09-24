from functools import wraps
from flask import request, jsonify

from flask_jwt_extended import verify_jwt_in_request, get_jwt_claims


def get_role():
  return get_jwt_claims()["role"]


def is_super_admin():
  return get_role() == "super_admin"


def is_admin():
  return get_role() == "admin" or is_super_admin()


def super_admin_required(fn):
  @wraps(fn)
  def wrapper(*args, **kwargs):
    verify_jwt_in_request()
    claims = get_jwt_claims()
    if is_super_admin():
      return fn(*args, **kwargs)
    else:
      return (
        jsonify(
          {
            "error": "UnauthorizedError",
            "message": "You are not authorized to access this resource",
          }
        ),
        403,
      )

  return wrapper


def admin_required(fn):
  @wraps(fn)
  def wrapper(*args, **kwargs):
    verify_jwt_in_request()
    claims = get_jwt_claims()
    if get_role() in set(["super_admin", "admin"]):
      return fn(*args, **kwargs)
    else:
      return (
        jsonify(
          {
            "error": "UnauthorizedError",
            "message": "You are not authorized to access this resource",
          }
        ),
        403,
      )

  return wrapper


def user_required(fn):
  @wraps(fn)
  def wrapper(*args, **kwargs):
    verify_jwt_in_request()
    claims = get_jwt_claims()
    if get_role() in set(["super_admin", "admin", "user"]):
      return fn(*args, **kwargs)
    else:
      return (
        jsonify(
          {
            "error": "UnauthorizedError",
            "message": "You are not authorized to access this resource",
          }
        ),
        403,
      )

  return wrapper
