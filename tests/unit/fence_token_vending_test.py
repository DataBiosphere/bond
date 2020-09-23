import unittest
from bond_app.fence_token_vending import FenceTokenVendingMachine
from werkzeug import exceptions

from mock import MagicMock
from bond_app.fence_api import FenceApi
from bond_app.oauth_adapter import OauthAdapter
from tests.unit.fake_token_store import FakeTokenStore
from tests.unit.fake_cache_api import FakeCacheApi
from tests.unit.fake_fence_token_storage import FakeFenceTokenStorage
import datetime
import string
import random

provider_name = "test"


class FenceTokenVendingMachineTestCase(unittest.TestCase):
    def setUp(self):
        self.cache_api = FakeCacheApi()
        self.refresh_token_store = FakeTokenStore()
        self.fence_token_storage = FakeFenceTokenStorage()

    def test_no_service_account(self):
        expected_json = 'fake service account json'
        real_user_id = self._random_subject_id()

        ftvm = FenceTokenVendingMachine(self._mock_fence_api(expected_json),
                                        self.cache_api, self.refresh_token_store,
                                        self._mock_oauth_adapter("fake_token"), provider_name,
                                        self.fence_token_storage)

        self.refresh_token_store.save(real_user_id, "fake_refresh_token", datetime.datetime.now(), "foo@bar.com", provider_name)

        service_account_json = ftvm.get_service_account_key_json(real_user_id)

        self.assertEqual(expected_json, service_account_json)

    def test_not_linked(self):
        real_user_id = self._random_subject_id()

        ftvm = FenceTokenVendingMachine(self._mock_fence_api(None), self.cache_api, self.refresh_token_store,
                                        None, provider_name, self.fence_token_storage)

        with self.assertRaises(exceptions.NotFound):
            ftvm.get_service_account_key_json(real_user_id)

    @staticmethod
    def _mock_fence_api(service_account_json):
        fence_api = FenceApi("")
        fence_api.get_credentials_google = MagicMock(return_value=service_account_json)
        return fence_api

    @staticmethod
    def _mock_oauth_adapter(access_token):
        oauth_adapter = OauthAdapter("", "", "", "")
        oauth_adapter.refresh_access_token = MagicMock(return_value={"access_token": access_token})
        return oauth_adapter

    @staticmethod
    def _random_subject_id():
        return ''.join(random.choice(string.digits) for _ in list(range(21)))
