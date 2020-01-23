import unittest
from google.appengine.api import memcache
from google.appengine.ext import ndb
from google.appengine.ext import testbed
import threading
from fence_token_vending import FenceTokenVendingMachine
from authentication import UserInfo
from memcache_api import MemcacheApi
from mock import MagicMock
from fence_api import FenceApi
from sam_api import SamApi
from oauth_adapter import OauthAdapter
from fence_token_storage import build_fence_service_account_key, FenceServiceAccount, FenceTokenStorage
from fence_token_storage import ServiceAccountNotUpdatedException
from token_store import TokenStore
import datetime
import string
import random
import endpoints
import time
from sam_api import SamKeys

provider_name = "test"


class FenceTokenVendingMachineTestCase(unittest.TestCase):
    def setUp(self):
        # First, create an instance of the Testbed class.
        self.testbed = testbed.Testbed()
        # Then activate the testbed, which prepares the service stubs for use.
        self.testbed.activate()
        # Next, declare which service stubs you want to use.
        self.testbed.init_memcache_stub()
        self.testbed.init_datastore_v3_stub()

        self.cache_api = MemcacheApi()

    def tearDown(self):
        ndb.get_context().clear_cache()  # Ensure data is truly flushed from datastore/memcache
        self.testbed.deactivate()

    def test_no_service_account(self):
        expected_json = 'fake service account json'
        caller_uid = self._random_subject_id()
        real_user_id = self._random_subject_id()

        ftvm = FenceTokenVendingMachine(self._mock_fence_api(expected_json),
                                        self._mock_sam_api(real_user_id, "foo@bar.com"),
                                        self.cache_api,
                                        self._mock_oauth_adapter("fake_token"), provider_name,
                                        FenceTokenStorage())

        TokenStore.save(real_user_id, "fake_refresh_token", datetime.datetime.now(), "foo@bar.com", provider_name)

        self.assertIsNone(self.cache_api.get(namespace=provider_name, key=caller_uid))
        fsa_key = build_fence_service_account_key(ftvm.provider_name, real_user_id)
        self.assertIsNone(fsa_key.get())

        service_account_json = ftvm.get_service_account_key_json(
            UserInfo(caller_uid, "splat@bar.com", "fake_token_too", 10))

        self.assertEqual(expected_json, service_account_json)
        self.assertIsNotNone(self.cache_api.get(namespace=provider_name, key=caller_uid))
        stored_fsa = fsa_key.get()
        self.assertIsNotNone(stored_fsa)
        self.assertIsNone(stored_fsa.update_lock_timeout)
        self.assertEqual(expected_json, stored_fsa.key_json)
        self.assertGreater(stored_fsa.expires_at, datetime.datetime.now())

    def test_active_service_account_in_locked_storage(self):
        expected_json = 'fake service account json'
        caller_uid = self._random_subject_id()
        real_user_id = self._random_subject_id()

        ftvm = FenceTokenVendingMachine(self._mock_fence_api(None), self._mock_sam_api(real_user_id, "foo@bar.com"),
                                        self.cache_api, self._mock_oauth_adapter("fake_token"), provider_name,
                                        FenceTokenStorage())

        TokenStore.save(real_user_id, "fake_refresh_token", datetime.datetime.now(), "foo@bar.com", provider_name)

        fsa_key = build_fence_service_account_key(ftvm.provider_name, real_user_id)
        stored_fsa = FenceServiceAccount(key_json=expected_json,
                                         expires_at=datetime.datetime.now() + datetime.timedelta(days=5),
                                         update_lock_timeout=None,
                                         key=fsa_key)
        stored_fsa.put()

        self.assertIsNone(self.cache_api.get(namespace=provider_name, key=caller_uid))

        service_account_json = ftvm.get_service_account_key_json(
            UserInfo(caller_uid, "splat@bar.com", "fake_token_too", 10))

        self.assertEqual(expected_json, service_account_json)
        self.assertIsNotNone(self.cache_api.get(namespace=provider_name, key=caller_uid))

    def test_active_service_account_in_cache(self):
        expected_json = 'fake service account json'
        caller_uid = self._random_subject_id()
        real_user_id = self._random_subject_id()

        ftvm = FenceTokenVendingMachine(None, None, self.cache_api, None, provider_name,
                                        None)  # none of the apis should be called

        self.cache_api.add(namespace=provider_name, key=caller_uid, value=expected_json, expires_in=20)

        fsa_key = build_fence_service_account_key(ftvm.provider_name, real_user_id)
        self.assertIsNone(fsa_key.get())

        service_account_json = ftvm.get_service_account_key_json(
            UserInfo(caller_uid, "splat@bar.com", "fake_token_too", 10))

        self.assertEqual(expected_json, service_account_json)
        self.assertIsNone(fsa_key.get())

    def test_expired_service_account_in_ds(self):
        self._test_with_lock(None)

    def test_already_locked_service_account_not_updated(self):
        with self.assertRaises(ServiceAccountNotUpdatedException):
            self._test_with_lock(datetime.datetime.now() + datetime.timedelta(seconds=2))

    def test_already_locked_service_account_updated(self):
        def update_fsa(fsa_key, expected_json):
            time.sleep(1)
            fsa = fsa_key.get()
            fsa.key_json = expected_json
            fsa.update_lock_timeout = None
            fsa.expires_at = datetime.datetime.now() + datetime.timedelta(days=5)
            fsa.put()

        self._test_with_lock(datetime.datetime.now() + datetime.timedelta(seconds=10), update_fsa, "not right")

    def test_expired_locked_service_account(self):
        self._test_with_lock(datetime.datetime.now() - datetime.timedelta(days=1))

    def _test_with_lock(self, lock_timeout, update_fsa_fxn=None, api_json=None):
        expected_json = 'fake service account json'
        if not api_json:
            api_json = expected_json
        caller_uid = self._random_subject_id()
        real_user_id = self._random_subject_id()

        ftvm = FenceTokenVendingMachine(self._mock_fence_api(api_json), self._mock_sam_api(real_user_id, "foo@bar.com"),
                                        self.cache_api, self._mock_oauth_adapter("fake_token"), provider_name,
                                        FenceTokenStorage())

        TokenStore.save(real_user_id, "fake_refresh_token", datetime.datetime.now(), "foo@bar.com", provider_name)

        fsa_key = build_fence_service_account_key(ftvm.provider_name, real_user_id)
        stored_fsa = FenceServiceAccount(key_json="expired json",
                                         expires_at=datetime.datetime.now() - datetime.timedelta(days=5),
                                         update_lock_timeout=lock_timeout,
                                         key=fsa_key)
        stored_fsa.put()

        self.assertIsNone(self.cache_api.get(namespace=provider_name, key=caller_uid))

        if update_fsa_fxn:
            threading.Thread(target=update_fsa_fxn, args=(fsa_key, expected_json)).start()

        service_account_json = ftvm.get_service_account_key_json(
            UserInfo(caller_uid, "splat@bar.com", "fake_token_too", 10))

        self.assertEqual(expected_json, service_account_json)
        self.assertIsNotNone(self.cache_api.get(namespace=provider_name, key=caller_uid))
        stored_fsa = fsa_key.get()
        self.assertIsNotNone(stored_fsa)
        self.assertIsNone(stored_fsa.update_lock_timeout)
        self.assertEqual(expected_json, stored_fsa.key_json)
        self.assertGreater(stored_fsa.expires_at, datetime.datetime.now())

    def test_not_linked(self):
        caller_uid = self._random_subject_id()
        real_user_id = self._random_subject_id()

        ftvm = FenceTokenVendingMachine(self._mock_fence_api(None), self._mock_sam_api(real_user_id, "foo@bar.com"),
                                        self.cache_api, None, provider_name, FenceTokenStorage())

        self.assertIsNone(self.cache_api.get(namespace=provider_name, key=caller_uid))
        fsa_key = build_fence_service_account_key(ftvm.provider_name, real_user_id)
        self.assertIsNone(fsa_key.get())

        with self.assertRaises(endpoints.BadRequestException):
            ftvm.get_service_account_key_json(UserInfo(caller_uid, "splat@bar.com", "fake_token_too", 10))

    @staticmethod
    def _mock_fence_api(service_account_json):
        fence_api = FenceApi("")
        fence_api.get_credentials_google = MagicMock(return_value=service_account_json)
        return fence_api

    @staticmethod
    def _mock_sam_api(subject_id, email):
        sam_api = SamApi("")
        sam_api.user_info = MagicMock(return_value={SamKeys.USER_ID_KEY: subject_id, SamKeys.USER_EMAIL_KEY: email})
        return sam_api

    @staticmethod
    def _mock_oauth_adapter(access_token):
        oauth_adapter = OauthAdapter("", "", "", "")
        oauth_adapter.refresh_access_token = MagicMock(return_value={"access_token": access_token})
        return oauth_adapter

    @staticmethod
    def _random_subject_id():
        return ''.join(random.choice(string.digits) for _ in range(21))
