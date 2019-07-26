import api

def test_app(client):
  assert client.get('/healthcheck').status_code == 200
