import { execFileSync } from "node:child_process"
import process from "node:process"

// Fresh e2e DB state: user 1 with secret "test", no boards/labels.
// Same DB_PATH as backend webServer in playwright.config.ts
const SEED = `
from sqlmodel import Session, delete
from app import crud
from app.core.db import get_engine
from app.core.security import hash_secret
from app.models import Board, Label, User
crud.init_db()
with Session(get_engine()) as s:
    s.exec(delete(Board))
    s.exec(delete(Label))
    user = s.get(User, 1)
    user.secret_hashed = hash_secret("test")
    s.add(user)
    s.commit()
`

export default function globalSetup() {
  // eslint-disable-next-line sonarjs/no-os-command-from-path -- dev/CI tool from PATH
  execFileSync("uv", ["run", "--no-build", "python", "-c", SEED], {
    cwd: "../backend",
    env: {
      ...process.env,
      DB_PATH: "sqlite-e2e.db",
      JWT_SECRET_KEY: "e2e-secret-e2e-secret-e2e-secret-e2e",
    },
    stdio: "inherit",
  })
}
