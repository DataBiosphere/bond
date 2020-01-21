# Datastore Emulator Tests
These are tests that require Datastore to run. The Datastore Emulator allows us to run these tests with some environment
modifications.

See https://cloud.google.com/datastore/docs/tools/datastore-emulator

## Running Locally
### One time setup
Do the one time setup of installing the Datastore Emulator.

`gcloud components install cloud-datastore-emulator`

### Testing 
Start the emulator:

`gcloud beta emulators datastore start --no-store-on-disk --project="test" --host-port=0.0.0.0:8432`

In another terminal, run the test script. Note that this sets (and attempts to unset) environment variables.

`./tests/datastore_emulator/test.sh`

Stop the emulator. (ctrl+C)