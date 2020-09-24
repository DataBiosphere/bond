import unittest

from werkzeug import exceptions
from mock import MagicMock

from bond_app.authentication import Authentication, AuthenticationConfig, UserInfo
from bond_app.sam_api import SamApi, SamKeys
from tests.unit.fake_cache_api import FakeCacheApi
import json


class TestRequestState:
    def __init__(self, auth_header):
        self.headers = {}
        if auth_header is not None:
            self.headers['Authorization'] = auth_header


class AuthenticationTestCase(unittest.TestCase):

    def setUp(self):
        self.cache_api = FakeCacheApi()
        self.sam_api = SamApi("")
        self.auth = Authentication(AuthenticationConfig(['32555940559'], ['.gserviceaccount.com'], 600),
                                   self.cache_api, self.sam_api)

    def test_good_user_no_cached_info(self):
        token = "testtoken"
        expected_user_info = UserInfo("193481341723041", "foo@bar.com", token, 100)
        self.sam_api.user_info = MagicMock(
            return_value=self._generate_sam_user_info(expected_user_info.id, expected_user_info.email, True))

        def token_fn(token):
            token_data = {
                "audience": "32555940559.apps.googleusercontent.com",
                "user_id": expected_user_info.id,
                "expires_in": expected_user_info.expires_in,
                "email": expected_user_info.email,
                "verified_email": True
            }
            return json.dumps(token_data)

        sam_user_id = self.auth.require_user_info(TestRequestState('bearer ' + token), token_fn)
        self.assertEqual(expected_user_info.id, sam_user_id)

    def test_good_user_sam_info_cached(self):
        token = "testtoken"
        expected_user_info = UserInfo("193481341723041", "foo@bar.com", token, 100)
        self.cache_api.add(namespace="SamUserInfo", key=expected_user_info.id, expires_in=0,
                           value=self._generate_sam_user_info(expected_user_info.id, expected_user_info.email, True))

        def token_fn(token):
            token_data = {
                "audience": "32555940559.apps.googleusercontent.com",
                "user_id": expected_user_info.id,
                "expires_in": expected_user_info.expires_in,
                "email": expected_user_info.email,
                "verified_email": True
            }
            return json.dumps(token_data)

        sam_user_id = self.auth.require_user_info(TestRequestState('bearer ' + token), token_fn)
        self.assertEqual(expected_user_info.id, sam_user_id)

    def test_good_user_google_info_cached(self):
        token = "testtoken"
        expected_user_info = UserInfo("193481341723041", "foo@bar.com", token, 100)
        self.cache_api.add(namespace="SamUserInfo", key=expected_user_info.id, expires_in=0,
                           value=self._generate_sam_user_info(expected_user_info.id, expected_user_info.email, True))

        def token_fn(token):
            token_data = {
                "audience": "32555940559.apps.googleusercontent.com",
                "user_id": expected_user_info.id,
                "expires_in": expected_user_info.expires_in,
                "email": expected_user_info.email,
                "verified_email": True
            }
            return json.dumps(token_data)

        self.auth.require_user_info(TestRequestState('bearer ' + token), token_fn)

        def token_fn2(token):
            raise Exception("shouldn't be called")

        sam_user_id = self.auth.require_user_info(TestRequestState('bearer ' + token), token_fn2)
        self.assertEqual(expected_user_info.id, sam_user_id)

    def test_good_user_cache_expire_token(self):
        token = "testtoken"
        expected_user_info = UserInfo("193481341723041", "foo@bar.com", token, 1)
        self.cache_api.add(namespace="SamUserInfo", key=expected_user_info.id, expires_in=0,
                           value=self._generate_sam_user_info(expected_user_info.id, expected_user_info.email, True))

        def token_fn(token):
            token_data = {
                "audience": "32555940559.apps.googleusercontent.com",
                "user_id": expected_user_info.id,
                "expires_in": expected_user_info.expires_in,
                "email": expected_user_info.email,
                "verified_email": True
            }
            return json.dumps(token_data)

        self.auth.require_user_info(TestRequestState('bearer ' + token), token_fn)

        def token_fn2(token):
            raise Exception("should detect this exception")

        import time
        time.sleep(2)

        with self.assertRaises(Exception):
            self.auth.require_user_info(TestRequestState('bearer ' + token), token_fn2)

    def test_good_user_cache_expire_config(self):
        auth = Authentication(AuthenticationConfig(['32555940559'], ['.gserviceaccount.com'], 1),
                              self.cache_api, self.sam_api)
        token = "testtoken"
        expected_user_info = UserInfo("193481341723041", "foo@bar.com", token, 100)
        self.cache_api.add(namespace="SamUserInfo", key=expected_user_info.id, expires_in=0,
                           value=self._generate_sam_user_info(expected_user_info.id, expected_user_info.email, True))

        def token_fn(token):
            token_data = {
                "audience": "32555940559.apps.googleusercontent.com",
                "user_id": expected_user_info.id,
                "expires_in": expected_user_info.expires_in,
                "email": expected_user_info.email,
                "verified_email": True
            }
            return json.dumps(token_data)

        auth.require_user_info(TestRequestState('bearer ' + token), token_fn)

        def token_fn2(token):
            raise Exception("should detect this exception")

        import time
        time.sleep(2)

        with self.assertRaises(Exception):
            auth.require_user_info(TestRequestState('bearer ' + token), token_fn2)

    def test_good_service_account(self):
        pet_token = "testtoken"
        user_token = "differenttoken"
        pet_info = UserInfo("193481341723041", "foo@bar.gserviceaccount.com", pet_token, 100)
        user_info = UserInfo("234567890123456", "foos_owner@bar.com", user_token, 100)
        self.cache_api.add(namespace="SamUserInfo", key=pet_info.id, expires_in=0,
                           value=self._generate_sam_user_info(user_info.id, user_info.email, True))

        def token_fn(token):
            token_data = {
                "audience": pet_info.id,
                "user_id": pet_info.id,
                "expires_in": pet_info.expires_in,
                "email": pet_info.email,
                "verified_email": True
            }
            return json.dumps(token_data)

        sam_user_id = self.auth.require_user_info(TestRequestState('bearer ' + pet_token), token_fn)
        self.assertEqual(user_info.id, sam_user_id)

    def test_user_disabled_in_sam(self):
        token = "testtoken"
        expected_user_info = UserInfo("193481341723041", "foo@bar.com", token, 100)
        self.sam_api.user_info = MagicMock(
            return_value=self._generate_sam_user_info(expected_user_info.id, expected_user_info.email, False))

        def token_fn(token):
            token_data = {
                "audience": "32555940559.apps.googleusercontent.com",
                "user_id": expected_user_info.id,
                "expires_in": expected_user_info.expires_in,
                "email": expected_user_info.email,
                "verified_email": True
            }
            return json.dumps(token_data)

        with self.assertRaises(Exception):
            self.auth.require_user_info(TestRequestState('bearer ' + token), token_fn)

    def test_pets_user_disabled_in_sam(self):
        pet_token = "testtoken"
        user_token = "differenttoken"
        pet_info = UserInfo("193481341723041", "foo@bar.gserviceaccount.com", pet_token, 100)
        user_info = UserInfo("234567890123456", "foos_owner@bar.com", user_token, 100)
        self.cache_api.add(namespace="SamUserInfo", key=pet_info.id, expires_in=0,
                           value=self._generate_sam_user_info(user_info.id, user_info.email, False))

        def token_fn(token):
            token_data = {
                "audience": pet_info.id,
                "user_id": pet_info.id,
                "expires_in": pet_info.expires_in,
                "email": pet_info.email,
                "verified_email": True
            }
            return json.dumps(token_data)

        with self.assertRaises(Exception):
            self.auth.require_user_info(TestRequestState('bearer ' + pet_token), token_fn)

    def test_missing_auth_header(self):
        def token_fn(token):
            raise Exception("shouldn't be called")

        with self.assertRaises(exceptions.Unauthorized):
            self.auth.require_user_info(TestRequestState(None), token_fn)

    def _unauthorized_test(self, token_data):
        def token_fn(token):
            return json.dumps(token_data)

        with self.assertRaises(exceptions.Unauthorized):
            self.auth.require_user_info(TestRequestState('bearer testtoken'), token_fn)

    def test_missing_email(self):
        token_data = {
            "audience": "32555940559.apps.googleusercontent.com",
            "user_id": "193481341723041",
            "expires_in": 100,
            "verified_email": True
        }
        self._unauthorized_test(token_data)

    def test_unverified_email(self):
        token_data = {
            "audience": "32555940559.apps.googleusercontent.com",
            "user_id": "193481341723041",
            "expires_in": 100,
            "email": "foo@bar.com",
            "verified_email": False
        }
        self._unauthorized_test(token_data)

    def test_missing_user_id(self):
        token_data = {
            "audience": "32555940559.apps.googleusercontent.com",
            "expires_in": 100,
            "email": "foo@bar.com",
            "verified_email": True
        }
        self._unauthorized_test(token_data)

    def test_missing_audience(self):
        token_data = {
            "user_id": "193481341723041",
            "expires_in": 100,
            "email": "foo@bar.com",
            "verified_email": True
        }
        self._unauthorized_test(token_data)

    def test_unacceptable_audience(self):
        token_data = {
            "audience": "baaaaaad.apps.googleusercontent.com",
            "user_id": "193481341723041",
            "expires_in": 100,
            "email": "foo@bar.com",
            "verified_email": True
        }
        self._unauthorized_test(token_data)

    def test_missing_expires_in(self):
        token_data = {
            "audience": "32555940559.apps.googleusercontent.com",
            "user_id": "193481341723041",
            "email": "foo@bar.com",
            "verified_email": True
        }
        self._unauthorized_test(token_data)

    def test_unacceptable_expires_in_1(self):
        token_data = {
            "audience": "32555940559.apps.googleusercontent.com",
            "user_id": "193481341723041",
            "expires_in": -1,
            "email": "foo@bar.com",
            "verified_email": True
        }
        self._unauthorized_test(token_data)

    def test_unacceptable_expires_in_2(self):
        token_data = {
            "audience": "32555940559.apps.googleusercontent.com",
            "user_id": "193481341723041",
            "expires_in": "asdf",
            "email": "foo@bar.com",
            "verified_email": True
        }
        self._unauthorized_test(token_data)

    def _generate_sam_user_info(self, user_id, email, enabled):
        return {SamKeys.USER_ID_KEY: user_id, SamKeys.USER_EMAIL_KEY: email, SamKeys.USER_ENABLED_KEY: enabled}
