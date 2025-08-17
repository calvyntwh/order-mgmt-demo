#!/usr/bin/env bash
set -euo pipefail

# Basic smoke script: wait for ports to be open

wait_for() {
  host="$1"
  port="$2"
  timeout=${3:-60}
  echo "Waiting for $host:$port..."
  for i in $(seq 1 "$timeout"); do
    if nc -z "$host" "$port" >/dev/null 2>&1; then
      echo "$host:$port is up"
      return 0
    fi
    sleep 1
  done
  echo "Timeout waiting for $host:$port"
  return 1
}

wait_for localhost 5432 60
wait_for localhost 8001 60
wait_for localhost 8002 60
wait_for localhost 8000 60

echo "All services responding on expected ports — basic smoke check passed"
