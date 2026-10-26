#!/usr/bin/env bash
# Arranca API y web como daemons (double-fork), independientes de Cursor.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
RUN="$ROOT/.run"
API="$ROOT/apps/api"
WEB="$ROOT/apps/web"
NODE_BIN="/tmp/node-v22.19.0-darwin-arm64/bin"
PY="$API/.venv/bin/python"

mkdir -p "$RUN"
export PATH="$NODE_BIN:$PATH"

for port in 8000 5173; do
  pids="$(lsof -tiTCP:$port -sTCP:LISTEN 2>/dev/null || true)"
  [[ -n "${pids}" ]] && kill -9 ${pids} 2>/dev/null || true
done

# Mata instancias previas propias
for f in api.pid web.pid; do
  if [[ -f "$RUN/$f" ]]; then
    kill -9 "$(cat "$RUN/$f")" 2>/dev/null || true
    rm -f "$RUN/$f"
  fi
done

daemonize() {
  local name="$1"
  local workdir="$2"
  shift 2
  "$PY" - "$name" "$workdir" "$RUN" "$@" <<'PY'
import os, sys, subprocess, pathlib
name, workdir, rundir, *cmd = sys.argv[1:]
rundir = pathlib.Path(rundir)
log = open(rundir / f"{name}.log", "ab", buffering=0)

# double-fork
if os.fork() > 0:
    sys.exit(0)
os.setsid()
if os.fork() > 0:
    sys.exit(0)

os.chdir(workdir)
os.environ["MONTI_DATABASE_URL"] = "sqlite:///./monti.sqlite3"
# Cargar .env de la API sin pisar MONTI_DATABASE_URL
env_path = pathlib.Path(workdir) / ".env"
if env_path.exists() and name == "api":
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        if k == "MONTI_DATABASE_URL":
            continue
        os.environ.setdefault(k, v.strip().strip('"').strip("'"))

os.dup2(log.fileno(), 1)
os.dup2(log.fileno(), 2)
proc = subprocess.Popen(cmd, cwd=workdir, start_new_session=True)
(rundir / f"{name}.pid").write_text(str(proc.pid))
sys.exit(0)
PY
}

# Cargar env para el proceso API vía el daemon (el .env se lee dentro)
daemonize api "$API" \
  "$PY" -m uvicorn monti.main:app --host 127.0.0.1 --port 8000

daemonize web "$WEB" \
  "$(command -v npx)" vite --host 127.0.0.1 --port 5173

sleep 2
for i in $(seq 1 15); do
  if curl -sf -m 1 http://127.0.0.1:8000/docs >/dev/null \
     && curl -sf -m 1 http://127.0.0.1:5173/ >/dev/null; then
    echo "OK"
    echo "  Web: http://127.0.0.1:5173/login"
    echo "  API: http://127.0.0.1:8000/docs"
    echo "  PIDs: api=$(cat "$RUN/api.pid") web=$(cat "$RUN/web.pid")"
    exit 0
  fi
  sleep 1
done

echo "No respondieron a tiempo. Logs:"
tail -n 30 "$RUN/api.log" || true
tail -n 30 "$RUN/web.log" || true
exit 1
