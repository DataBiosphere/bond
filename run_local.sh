#!/usr/bin/env bash

export FLASK_APP=main.py
# Configure the app to talk to the Datastore Emulator.
export DATASTORE_EMULATOR_HOST=0.0.0.0:8432

FLASK_HOST="${1:-localhost}"

flask run --debugger -p 8080 -h $FLASK_HOST
