import requests
from google.cloud import ndb
from google.auth.credentials import AnonymousCredentials

# The project should match the project given to the Datastore Emulator.
# Use anonymous credentials for testing.
client = ndb.Client(project="test", credentials=AnonymousCredentials())


def setUp(testcase):
    """Function to call before each datastore emulator test."""
    # Establish an NDB Client Context for each test and clean it up afterwards.
    ndb_context = client.context()
    ndb_context.__enter__()
    testcase.addCleanup(ndb_context.__exit__, None, None, None)

    # Disable memcache for this test as we're not emulating a memcache environment and we will raise errors
    # as ndb tries to use memcache by default.
    ndb.get_context().set_memcache_policy(False)
    # Disable caching so that values don't stick around between tests.
    ndb.get_context().set_cache_policy(False)

    # Reset the contents of the Datastore emulator on cleanup. Host:port as specified in README.md
    testcase.addCleanup(requests.post, 'http://0.0.0.0:8432/reset')
