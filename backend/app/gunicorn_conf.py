"""Config file for Gunicorn for prod deployment on entorb.net."""

# run manually
# ~/.local/bin/gunicorn --config ~/todo/app/gunicorn_conf.py
# run via supervisorctl
# supervisorctl restart todo-fastapi
# see log
# tail -f ~/logs/supervisord.log

import os

app_path = os.environ["HOME"] + "/be/todo/"

wsgi_app = "app.main:app"
bind = ":9003"
chdir = app_path

# SQLite: few workers are enough
workers = 2
worker_class = "uvicorn.workers.UvicornWorker"

# trust X-Forwarded-For only from the local reverse proxy,
# required for the per-IP login rate limit
forwarded_allow_ips = "127.0.0.1,::1"

timeout = 30
graceful_timeout = 30
keepalive = 5

# Worker lifecycle - restart workers periodically to prevent memory leaks
max_requests = 1000
max_requests_jitter = 50

errorlog = app_path + "error.log"
accesslog = app_path + "access.log"
loglevel = "info"
