from fence_token_storage import create_fence_service_account_key, FenceServiceAccount, FenceTokenStorage, \
    ServiceAccountNotUpdatedException, _FSA_KEY_LIFETIME
from google.appengine.ext import ndb
from google.appengine.ext import testbed
import datetime
import threading
import time
import unittest


class FenceTokenStorageTestCase(unittest.TestCase):

    def setUp(self):
        # First, create an instance of the Testbed class.
        self.testbed = testbed.Testbed()
        # Then activate the testbed, which prepares the service stubs for use.
        self.testbed.activate()
        # Next, declare which service stubs you want to use.
        self.testbed.init_memcache_stub()
        self.testbed.init_datastore_v3_stub()

        # How many times fence_fetch has been called.
        self.fence_fetches = 0

        # Set up some default values.
        self.user_id = "default_user_id"
        self.provider_name = "default_provider"
        self.fsa_key = create_fence_service_account_key(self.provider_name, self.user_id)

    def prep_key(self, fsa_key):
        """Dummy function to use to prep keys. """
        return "prepped: " + fsa_key.string_id()

    def fence_fetch(self, prepped_key):
        """Dummy function to fetch a fence credential. Increments fence_fetches with every call. """
        self.fence_fetches = self.fence_fetches + 1
        return "json_value: " + prepped_key

    def assertIsExpectedToken(self, key_json):
        """Asserts that key_json is equal to the default expected token value."""
        self.assertEqual(key_json, "json_value: prepped: default_provider")

    def tearDown(self):
        ndb.get_context().clear_cache()  # Ensure data is truly flushed from datastore/memcache
        self.testbed.deactivate()

    def test_create(self):
        token_storage = FenceTokenStorage()

        (key_json, expires_at) = token_storage.get_or_create(self.fsa_key, prep_key_fn=self.prep_key,
                                                             fence_fetch_fn=self.fence_fetch)

        self.assertIsExpectedToken(key_json)
        self.assertAlmostEqual(expires_at, datetime.datetime.now() + _FSA_KEY_LIFETIME,
                               delta=datetime.timedelta(seconds=5))
        self.assertEqual(self.fence_fetches, 1)

        fence_service_account = self.fsa_key.get()
        self.assertEqual(key_json, fence_service_account.key_json)
        self.assertEqual(expires_at, fence_service_account.expires_at)
        self.assertIsNone(fence_service_account.update_lock_timeout)

    def test_sequential_gets(self):
        token_storage = FenceTokenStorage()

        # First get_or_create should create and store credentials
        result1 = token_storage.get_or_create(self.fsa_key, prep_key_fn=self.prep_key,
                                              fence_fetch_fn=self.fence_fetch)
        self.assertEqual(self.fence_fetches, 1)

        # Second get_or_create should fetch the existing credentials.
        result2 = token_storage.get_or_create(self.fsa_key, prep_key_fn=self.prep_key,
                                              fence_fetch_fn=self.fence_fetch)

        self.assertEqual(self.fence_fetches, 1)
        self.assertEqual(result1, result2)

    def test_expired_token_recreated(self):
        # Store an expired key
        FenceServiceAccount(key=self.fsa_key, key_json="expired_key",
                            expires_at=datetime.datetime.now() - datetime.timedelta(minutes=1),
                            update_lock_timeout=None).put()

        token_storage = FenceTokenStorage()
        (key_json, expires_at) = token_storage.get_or_create(self.fsa_key, prep_key_fn=self.prep_key,
                                                             fence_fetch_fn=self.fence_fetch)
        self.assertIsExpectedToken(key_json)
        self.assertEqual(self.fence_fetches, 1)

    def test_waits_for_lock_update(self):
        # Store a lock on the key.
        FenceServiceAccount(key=self.fsa_key, key_json=None, expires_at=None,
                            update_lock_timeout=datetime.datetime.now() + datetime.timedelta(minutes=1)).put()

        def unlock_and_set_key():
            """Sleep a second before setting the key and clearing the lock."""
            time.sleep(1)
            FenceServiceAccount(key=self.fsa_key, key_json="updated",
                                expires_at=datetime.datetime.now() + datetime.timedelta(minutes=1),
                                update_lock_timeout=None).put()

        threading.Thread(target=unlock_and_set_key).run()

        token_storage = FenceTokenStorage()
        (key_json, _) = token_storage.get_or_create(self.fsa_key, prep_key_fn=self.prep_key,
                                                    fence_fetch_fn=self.fence_fetch)
        self.assertEqual(key_json, "updated")
        self.assertEqual(self.fence_fetches, 0)

    def test_waits_for_lock_no_update_throws(self):
        # Store a lock on the key, but let the lock expire without setting a value.
        FenceServiceAccount(key=self.fsa_key, key_json=None, expires_at=None,
                            update_lock_timeout=datetime.datetime.now() + datetime.timedelta(seconds=1)).put()

        token_storage = FenceTokenStorage()
        with self.assertRaises(ServiceAccountNotUpdatedException):
            print token_storage.get_or_create(self.fsa_key, prep_key_fn=self.prep_key,
                                        fence_fetch_fn=self.fence_fetch)

    def test_delete(self):
        token_storage = FenceTokenStorage()
        (key_json, _) = token_storage.get_or_create(self.fsa_key, prep_key_fn=self.prep_key,
                                                    fence_fetch_fn=self.fence_fetch)
        self.assertEqual(self.fence_fetches, 1)
        self.assertIsExpectedToken(key_json)

        token_storage.delete(self.fsa_key)
        self.assertIsNone(self.fsa_key.get())

    def test_delete_nonexistant(self):
        token_storage = FenceTokenStorage()
        self.assertIsNone(token_storage.delete(self.fsa_key))
        self.assertIsNone(self.fsa_key.get())