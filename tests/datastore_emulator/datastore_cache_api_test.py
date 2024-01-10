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

    def test_large_keys(self):
        cache = DatastoreCacheApi()

        large_key = b64encode(os.urandom(1600)).decode('utf-8')

        # Keys over 1500 bytes should not be added to cache but handled gracefully.
        self.assertFalse(cache.add(large_key, "value"))
        self.assertIsNone(cache.get(large_key))
        cache.delete(large_key)
