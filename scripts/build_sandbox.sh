#!/bin/bash
# Build the swebench-sandbox:latest image the harness runs tasks in (Python 3.13, git, pytest),
# with the public offline wheels mounted at /wheels, from the competition's own Dockerfile.
set -euo pipefail
cd "$(dirname "$0")/../data"
ctx=$(mktemp -d)
trap 'rm -rf "$ctx"' EXIT
cp docker/Dockerfile.public docker/imp.py docker/telnetlib.py "$ctx"/
cp -R wheels "$ctx"/wheels
docker build --platform linux/amd64 -t swebench-sandbox:latest -f "$ctx/Dockerfile.public" "$ctx"
