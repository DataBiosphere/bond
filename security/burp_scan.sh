#!/usr/bin/env bash

set -eu

# Burp private Docker image URL (this assumes the client was already
# authenticated with container registry using burp_start.sh)
IMAGE="$1"

#Check proxy config
python3 BroadBurpScanner.py http://localhost --action proxy-config


# Scan collected traffic and report results (optional)
docker run --rm -it --entrypoint /automation/BroadBurpScanner.py "${IMAGE}" \
  http://localhost --action scan