# How to deploy to Uberspace U8 / entorb.net

Layout on webserver:

- `~/html/todo/` — built frontend (`frontend/dist`)
- `~/be/todo/` — backend: `app/`, `scripts/`, `requirements.txt`, `.env`, `db.sqlite`

## Initial setup

Plain uvicorn, no gunicorn (few users, saves RAM). Installed via `requirements.txt` by `scripts/deploy.sh`.
Logs go to journald.

```sh
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

see [fastapi-todo.service](backend/app/fastapi-todo.service)

```sh
# update services (after changing the .service file)
cp ~/be/todo/app/fastapi-todo.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now fastapi-todo
# restart
systemctl --user restart fastapi-todo
# status
systemctl --user status fastapi-todo
# logs
journalctl --user -u fastapi-todo -f
```

## Register backend

```sh
uberspace web backend add /be/todo port 9003
uberspace web backend list
```

The login rate limit uses `X-Forwarded-For`, trusted only from `127.0.0.1,::1` (see `--forwarded-allow-ips` in [fastapi-todo.service](backend/app/fastapi-todo.service)). Verify in `journalctl --user -u fastapi-todo` that real client IPs show up.
