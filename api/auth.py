from functools import wraps
from flask import abort

from flask_jwt_extended import verify_jwt_in_request, get_jwt_claims


def get_role():
  return get_jwt_claims()["role"]


def is_super_admin():
  return get_role() == "super_admin"


def is_admin():
  return get_role() == "admin" or is_super_admin()


def abortUnauthorized():
  abort(
    403, "You are not authorized to access this resource", error="UnauthorizedError"
  )


def unauthorized():
  return (
    {
      "error": "UnauthorizedError",
      "message": "You are not authorized to access this resource",
    },
    403,
  )


def super_admin_required(fn):
  @wraps(fn)
  def wrapper(*args, **kwargs):
    verify_jwt_in_request()
    if is_super_admin():
      return fn(*args, **kwargs)
    else:
      return unauthorized()

  return wrapper


def admin_required(fn):
  @wraps(fn)
  def wrapper(*args, **kwargs):
    verify_jwt_in_request()
    if get_role() in set(["super_admin", "admin"]):
      return fn(*args, **kwargs)
    else:
      return unauthorized()

  return wrapper


def user_required(fn):
  @wraps(fn)
  def wrapper(*args, **kwargs):
    verify_jwt_in_request()
    if get_role() in set(["super_admin", "admin", "user"]):
      return fn(*args, **kwargs)
    else:
      return unauthorized()

  return wrapper
