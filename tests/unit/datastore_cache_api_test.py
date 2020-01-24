import time
import unittest

from datastore_cache_api import DatastoreCacheApi
from google.appengine.ext import ndb
from google.appengine.ext import testbed
from tests.unit import cache_api_test


class DatstoreCacheApiTestCase(unittest.TestCase, cache_api_test.CacheApiTest):
    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_memcache_stub()
        self.testbed.init_datastore_v3_stub()
        self.setUpCache(DatastoreCacheApi())

    def tearDown(self):
        ndb.get_context().clear_cache()  # Ensure data is truly flushed from memcache
        self.testbed.deactivate()

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
