import unittest

from google.appengine.api import memcache
from google.appengine.ext import testbed
from werkzeug import exceptions

import authentication
from memcache_api import MemcacheApi
import json


class TestRequestState:
    def __init__(self, auth_header):
        self.headers = {}
        if auth_header is not None:
            self.headers['Authorization'] = auth_header


class AuthenticationTestCase(unittest.TestCase):

    def setUp(self):
        # First, create an instance of the Testbed class.
        self.testbed = testbed.Testbed()
        # Then activate the testbed, which prepares the service stubs for use.
        self.testbed.activate()
        # Next, declare which service stubs you want to use.
        self.testbed.init_memcache_stub()
        self.cache_api = MemcacheApi()
        self.auth = authentication.Authentication(authentication.AuthenticationConfig(['32555940559'], ['.gserviceaccount.com'], 600), self.cache_api)

    def tearDown(self):
        self.testbed.deactivate()

    def test_good_user(self):
        token = "testtoken"
        expected_user_info = authentication.UserInfo("193481341723041", "foo@bar.com", token, 100)

        def token_fn(token):
            token_data = {
                "audience": "32555940559.apps.googleusercontent.com",
                "user_id": expected_user_info.id,
                "expires_in": expected_user_info.expires_in,
                "email": expected_user_info.email,
                "verified_email": True
            }
            return json.dumps(token_data)

        user_info = self.auth.require_user_info(TestRequestState('bearer ' + token), token_fn)
        self.assertEqual(expected_user_info, user_info)

    def test_good_user_cached(self):
        token = "testtoken"
        expected_user_info = authentication.UserInfo("193481341723041", "foo@bar.com", token, 100)

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

        user_info = self.auth.require_user_info(TestRequestState('bearer ' + token), token_fn2)
        self.assertEqual(expected_user_info, user_info)

    def test_good_user_cache_expire_token(self):
        token = "testtoken"
        expected_user_info = authentication.UserInfo("193481341723041", "foo@bar.com", token, 1)

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
        auth = authentication.Authentication(authentication.AuthenticationConfig(['32555940559'], ['.gserviceaccount.com'], 1), self.cache_api)
        token = "testtoken"
        expected_user_info = authentication.UserInfo("193481341723041", "foo@bar.com", token, 100)

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
        token = "testtoken"
        expected_user_info = authentication.UserInfo("193481341723041", "foo@bar.gserviceaccount.com", token, 100)

        def token_fn(token):
            token_data = {
                "audience": expected_user_info.id,
                "user_id": expected_user_info.id,
                "expires_in": expected_user_info.expires_in,
                "email": expected_user_info.email,
                "verified_email": True
            }
            return json.dumps(token_data)

        user_info = self.auth.require_user_info(TestRequestState('bearer ' + token), token_fn)
        self.assertEqual(expected_user_info, user_info)

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
