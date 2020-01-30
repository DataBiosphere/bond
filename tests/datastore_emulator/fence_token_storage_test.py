from fence_token_storage import ProviderUser, FenceServiceAccount, FenceTokenStorage, \
    ServiceAccountNotUpdatedException, _FSA_KEY_LIFETIME
import datetime
import threading
import time
import unittest
import datastore_emulator_utils


class FenceTokenStorageTestCase(unittest.TestCase):

    def setUp(self):
        # Make sure to run these tests with a Datastore Emulator running or else they will fail with 'InternalError.'
        # See the README in this directory.

        datastore_emulator_utils.setUp(self)

        # How many times fence_fetch has been called.
        self.fence_fetches = 0

        # Set up some default values.
        self.user_id = "default_user_id"
        self.provider_name = "default_provider"
        self.provider_user = ProviderUser(provider_name=self.provider_name, user_id=self.user_id)
        self.fsa_key = FenceTokenStorage._build_fence_service_account_key(self.provider_user)

    def prep_key(self, provider_user):
        """Dummy function to use to prep keys. """
        return "prepped: " + provider_user.provider_name

    def fence_fetch(self, prepped_key):
        """Dummy function to fetch a fence credential. Increments fence_fetches with every call. """
        self.fence_fetches = self.fence_fetches + 1
        return "json_value: " + prepped_key

    def assertIsExpectedToken(self, key_json):
        """Asserts that key_json is equal to the default expected token value."""
        self.assertEqual(key_json, "json_value: prepped: default_provider")

    def test_create(self):
        token_storage = FenceTokenStorage()

        (key_json, expires_at) = token_storage.retrieve(self.provider_user, prep_key_fn=self.prep_key,
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

        # First retrieve should create and store credentials
        result1 = token_storage.retrieve(self.provider_user, prep_key_fn=self.prep_key,
                                         fence_fetch_fn=self.fence_fetch)
        self.assertEqual(self.fence_fetches, 1)

        # Second retrieve should fetch the existing credentials.
        result2 = token_storage.retrieve(self.provider_user, prep_key_fn=self.prep_key,
                                         fence_fetch_fn=self.fence_fetch)

        self.assertEqual(self.fence_fetches, 1)
        self.assertEqual(result1, result2)

    def test_expired_token_recreated(self):
        # Store an expired key
        FenceServiceAccount(key=self.fsa_key, key_json="expired_key",
                            expires_at=datetime.datetime.now() - datetime.timedelta(minutes=1),
                            update_lock_timeout=None).put()

        token_storage = FenceTokenStorage()
        (key_json, expires_at) = token_storage.retrieve(self.provider_user, prep_key_fn=self.prep_key,
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
        (key_json, _) = token_storage.retrieve(self.provider_user, prep_key_fn=self.prep_key,
                                               fence_fetch_fn=self.fence_fetch)
        self.assertEqual(key_json, "updated")
        self.assertEqual(self.fence_fetches, 0)

    def test_waits_for_lock_no_update_throws(self):
        # Store a lock on the key, but let the lock expire without setting a value.
        FenceServiceAccount(key=self.fsa_key, key_json=None, expires_at=None,
                            update_lock_timeout=datetime.datetime.now() + datetime.timedelta(seconds=1)).put()

        token_storage = FenceTokenStorage()
        with self.assertRaises(ServiceAccountNotUpdatedException):
            print token_storage.retrieve(self.provider_user, prep_key_fn=self.prep_key,
                                         fence_fetch_fn=self.fence_fetch)

    def test_delete(self):
        token_storage = FenceTokenStorage()
        (key_json, _) = token_storage.retrieve(self.provider_user, prep_key_fn=self.prep_key,
                                               fence_fetch_fn=self.fence_fetch)
        self.assertEqual(self.fence_fetches, 1)
        self.assertIsExpectedToken(key_json)

        token_storage.delete(self.provider_user)
        self.assertIsNone(self.fsa_key.get())

    def test_delete_nonexistant(self):
        token_storage = FenceTokenStorage()
        self.assertIsNone(token_storage.delete(self.provider_user))
        self.assertIsNone(self.fsa_key.get())
