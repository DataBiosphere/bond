from base64 import b64encode
import os
import time
import unittest

from bond_app.datastore_cache_api import DatastoreCacheApi
from tests.unit import cache_api_test
from tests.datastore_emulator import datastore_emulator_utils


class DatstoreCacheApiTestCase(unittest.TestCase, cache_api_test.CacheApiTest):
    def setUp(self):
        datastore_emulator_utils.setUp(self)
        self.setUpCache(DatastoreCacheApi())

    def test_delete_removes_expired_entries(self):
        cache = DatastoreCacheApi()

        cache.add("foo", "foo_value", expires_in=0.5)
        cache.add("foo_namespace", "foo_namespace_value", expires_in=0.5, namespace="baz")
        cache.add("not_expired", "not_expired_value", expires_in=100)
        cache.add("no_expiration", "no_expiration_value")

        foo_key = DatastoreCacheApi._build_cache_key("foo", None)
        self.assertIsNotNone(foo_key.get())

        time.sleep(1)

        # Value expired, but entry is still present in Datastore.
        self.assertIsNone(cache.get("foo"))
        self.assertIsNotNone(foo_key.get())

        cache.delete_expired_entries()

        self.assertIsNone(foo_key.get())
        self.assertIsNone(DatastoreCacheApi._build_cache_key("foo_namespace", "baz").get())
        self.assertIsNotNone(DatastoreCacheApi._build_cache_key("not_expired", None).get())
        self.assertIsNotNone(DatastoreCacheApi._build_cache_key("no_expiration", None).get())

    def test_large_keys(self):
        cache = DatastoreCacheApi()

        large_key = b64encode(os.urandom(1600)).decode('utf-8')

        # Keys over 1500 bytes should not be added to cache but handled gracefully.
        self.assertFalse(cache.add(large_key, "value"))
        self.assertIsNone(cache.get(large_key))
        cache.delete(large_key)
