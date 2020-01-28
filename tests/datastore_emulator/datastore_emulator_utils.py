import requests
from google.cloud import ndb

def setUp():
    """Function to call before each datastore emulator test."""
    # Disable memcache for this test as we're not emulating a memcache environment and we will raise errors
    # as ndb tries to use memcache by default.
    ndb.get_context().set_memcache_policy(False)
    # Disable caching so that values don't stick around between tests.
    ndb.get_context().set_cache_policy(False)

def tearDown():
    """Function to call after each datastore emulator test."""
    # Reset the contents of the Datastore emulator. Host:port as specified in README.md
    requests.post('http://0.0.0.0:8432/reset')