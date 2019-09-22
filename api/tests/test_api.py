def test_app_health(client):
  assert client.get("/healthcheck").status_code == 200
