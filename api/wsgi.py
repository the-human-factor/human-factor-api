from api.app import create_app

if __name__ == '__main__':
  app.run(host=app.config.get('HOST', '0.0.0.0'), port=app.config.get('PORT', 9000))
