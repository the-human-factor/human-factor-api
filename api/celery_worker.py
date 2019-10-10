#!/usr/bin/env python
import os
from api.jobs import celery
from api.app import create_app


app = create_app()
app.app_context().push()
