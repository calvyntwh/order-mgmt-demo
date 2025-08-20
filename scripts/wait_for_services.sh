#!/usr/bin/env bash
# Wait for a list of host:port pairs to become available.
# Usage: ./scripts/wait_for_services.sh host1:port1 host2:port2 ...

set -euo pipefail

if [ "$#" -eq 0 ]; then
  echo "Usage: $0 host:port [host:port ...]"
  exit 2
fi

for target in "$@"; do
  host=$(echo "$target" | cut -d: -f1)
  port=$(echo "$target" | cut -d: -f2)
  echo "Waiting for $host:$port..."
  until nc -z "$host" "$port"; do
    sleep 1
  done
  echo "$host:$port is available"
done

echo "All targets are available"
