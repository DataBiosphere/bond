# Datastore Emulator Tests
These are tests that require Datastore to run. The Datastore Emulator allows us to run these tests with some environment
modifications.

See https://cloud.google.com/datastore/docs/tools/datastore-emulator

# Running Locally
## One time setup
Do the one time setup of installing the Datastore Emulator.

`gcloud components install cloud-datastore-emulator`

## Python2 Environment

Datastore emulator must be run with python2. The Datastore Emulator does not currently have support for running with python3.

Similar to virtualenv setup in the head [README](../../README.md), make sure you have a python2 available.
```python2 --version```

And create a virtualenv environment for python2.

```virtualenv -p python2 env2```

Activate the environment to run the datastore emulator.

```source env2/bin/activate```

## Testing 

Start the emulator:

`./tests/datastore_emulator/run_emulator.sh`

In another terminal, run the test script. Note that this sets (and attempts to unset) environment variables.

`./tests/datastore_emulator/test.sh`

Stop the emulator. (ctrl+C)
