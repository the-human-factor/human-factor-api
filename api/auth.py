from functools import wraps
from flask import request, jsonify

from flask_jwt_extended import verify_jwt_in_request, get_jwt_claims


def super_admin_required(fn):
  @wraps(fn)
  def wrapper(*args, **kwargs):
    verify_jwt_in_request()
    claims = get_jwt_claims()
    if claims["role"] == "super_admin":
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
    if claims["role"] in set(["super_admin", "admin"]):
      return (
        jsonify(
          {
            "error": "UnauthorizedError",
            "message": "You are not authorized to access this resource",
          }
        ),
        403,
      )
    else:
      return fn(*args, **kwargs)

  return wrapper


def user_required(fn):
  @wraps(fn)
  def wrapper(*args, **kwargs):
    verify_jwt_in_request()
    claims = get_jwt_claims()
    if claims["role"] in set(["super_admin", "admin", "user"]):
      return (
        jsonify(
          {
            "error": "UnauthorizedError",
            "message": "You are not authorized to access this resource",
          }
        ),
        403,
      )
    else:
      return fn(*args, **kwargs)

  return wrapper
