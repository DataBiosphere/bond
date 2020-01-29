#!/usr/bin/env bash
gcloud beta emulators datastore start --no-store-on-disk --project="test" --host-port=0.0.0.0:8432