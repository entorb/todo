# How to deploy to Uberspace / entorb.net

Layout on webserver:

- `~/html/todo/` — built frontend (`frontend/dist`)
- `~/be/todo/` — backend: `app/`, `scripts/`, `requirements.txt`, `.env`, `db.sqlite`

## Initial setup

```sh
pip3.14 install --user gunicorn
# uvloop httptools

# secret for JWT signing
mkdir -p ~/be
mkdir -p ~/be/todo
mkdir -p ~/be/todo/app
mkdir -p ~/be/todo/scripts
python3.14 -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_urlsafe(32))" > ~/be/todo/.env
```

Then run `./scripts/deploy.sh` locally and set the login secret of user 1:

```sh
cd ~/be/todo && python3.14 -m scripts.set_user_secret 1
```

Share a board with another user (card access only), by board key and user name:

```sh
cd ~/be/todo && python3.14 -m scripts.add_board_member s-week Torben
```

## Service

```sh
cp ~/be/todo/app/todo-fastapi.ini ~/etc/services.d/
supervisorctl reread
supervisorctl update
```

## Register backend

```sh
uberspace web backend list
uberspace web backend set be/todo --http --port 9003
```

The login rate limit uses `X-Forwarded-For`, trusted only from `127.0.0.1` (see `forwarded_allow_ips` in [gunicorn_conf.py](backend/app/gunicorn_conf.py)). Verify in `~/be/todo/access.log` that real client IPs show up.
