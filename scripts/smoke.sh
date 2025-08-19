#!/usr/bin/env bash
set -euo pipefail

# Robust smoke script
# - waits for TCP ports to accept connections
# - optionally checks HTTP /health endpoints if the port serves HTTP
# - configurable timeout and targets

TIMEOUT=60
HOST=localhost
declare -a PORTS=(5432 8001 8002 8000)

usage() {
  cat <<EOF
Usage: $0 [--timeout N] [--host HOST] [port1 port2 ...]

Defaults: --timeout $TIMEOUT --host $HOST
Examples:
  $0                 # checks default ports on localhost
  $0 --timeout 30 8000 8001
EOF
}

while [[ ${1:-} != "" ]]; do
  case "$1" in
    --timeout)
      TIMEOUT="$2"; shift 2;;
    --host)
      HOST="$2"; shift 2;;
    -h|--help)
      usage; exit 0;;
    *)
      # treat remaining args as ports
      PORTS=()
      while [[ ${1:-} != "" ]]; do
        PORTS+=("$1"); shift
      done
      ;;
  esac
done

wait_for_port() {
  local host="$1" port="$2" timeout="$3"
  echo "Waiting for ${host}:${port} (timeout ${timeout}s) ..."
  local start now elapsed
  start=$(date +%s)
  while :; do
    if nc -z "$host" "$port" >/dev/null 2>&1; then
      echo "${host}:${port} is accepting connections"
      return 0
    fi
    now=$(date +%s)
    elapsed=$((now - start))
    if (( elapsed >= timeout )); then
      echo "Timeout after ${timeout}s waiting for ${host}:${port}" >&2
      return 1
    fi
    sleep 1
  done
}

check_http_health() {
  local host="$1" port="$2"
  local url="http://${host}:${port}/health"
  # try a fast HTTP check (timeout 3s)
  if curl -sS --max-time 3 "$url" >/dev/null 2>&1; then
    echo "HTTP health OK: ${url}"
    return 0
  fi
  return 1
}

failures=0
for p in "${PORTS[@]}"; do
  if ! wait_for_port "$HOST" "$p" "$TIMEOUT"; then
    failures=$((failures+1))
    continue
  fi

  # If it's an HTTP port, try the /health endpoint
  if check_http_health "$HOST" "$p"; then
    continue
  else
    # non-HTTP ports or health endpoint not implemented - that's OK for DB ports
    echo "No HTTP health response on ${HOST}:${p} (this may be fine)"
  fi
done

if (( failures > 0 )); then
  echo "Smoke check failed: ${failures} target(s) did not become ready" >&2
  exit 2
fi

echo "All services responding on expected ports — basic smoke check passed"

