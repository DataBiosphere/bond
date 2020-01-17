#!/usr/bin/env bash


# Set up the environment variables so that the tests will use the emulator:
export DATASTORE_EMULATOR_HOST=0.0.0.0:8432
export DATASTORE_PROJECT_ID=broad-bond-dev
#$(gcloud beta emulators datastore env-init)
export DATASTORE_USE_PROJECT_ID_AS_APP_ID=true


# Run the tests
python tests/test_runner.py --test-path=tests/datastore_emulator $(gcloud info --format="value(installation.sdk_root)")
status="$?"


# Unset the environment variables.
unset DATASTORE_USE_PROJECT_ID_AS_APP_ID
#$(gcloud beta emulators datastore env-unset)
unset DATASTORE_EMULATOR_HOST
unset DATASTORE_PROJECT_ID

exit $status
