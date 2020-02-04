#!/usr/bin/env bash

# Set up the environment variables so that the tests will use the emulator:
export DATASTORE_EMULATOR_HOST=0.0.0.0:8432
export DATASTORE_PROJECT_ID=test
export DATASTORE_USE_PROJECT_ID_AS_APP_ID=true

# Run the tests
python -m unittest discover -s tests/datastore_emulator -p "*_test.py"
status="$?"

# Unset the environment variables.
unset DATASTORE_USE_PROJECT_ID_AS_APP_ID
unset DATASTORE_EMULATOR_HOST
unset DATASTORE_PROJECT_ID

exit $status
