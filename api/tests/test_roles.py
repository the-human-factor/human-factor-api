from api.auth import super_admin_required, admin_required, user_required

def test_super_admin_required(app, client, super_admin, admin, user, end_user):
  @app.route("/super-admin-endpoint")
  @super_admin_required
  def super_admin_endpoint():
    return "ok", 200

  resp = client.get("/super-admin-endpoint")
  assert resp.status_code == 401

  for u in [admin, user, end_user]:
    token = u.create_access_token_with_claims()
    resp = client.get(
      "/super-admin-endpoint", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 403

  token = super_admin.create_access_token_with_claims()
  resp = client.get(
    "/super-admin-endpoint", headers={"Authorization": f"Bearer {token}"}
  )
  assert resp.status_code == 200


def test_admin_required(app, client, super_admin, admin, user, end_user):
  @app.route("/admin-endpoint")
  @admin_required
  def admin_endpoint():
    return "ok", 200

  resp = client.get("/admin-endpoint")
  assert resp.status_code == 401

  for u in [super_admin, admin]:
    token = u.create_access_token_with_claims()
    resp = client.get("/admin-endpoint", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200

  for u in [user, end_user]:
    token = u.create_access_token_with_claims()
    resp = client.get("/admin-endpoint", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403


def test_user_required(app, client, super_admin, admin, user, end_user):
  @app.route("/user-endpoint")
  @user_required
  def user_endpoint():
    return "ok", 200

  resp = client.get("/user-endpoint")
  assert resp.status_code == 401

  for u in [super_admin, admin, user]:
    token = u.create_access_token_with_claims()
    resp = client.get("/user-endpoint", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200

  token = end_user.create_access_token_with_claims()
  resp = client.get("/user-endpoint", headers={"Authorization": f"Bearer {token}"})
  assert resp.status_code == 403
