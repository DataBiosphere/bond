import unittest

import memcache_api
from google.appengine.ext import ndb
from google.appengine.ext import testbed
import cache_api_test


class MemcacheApiTestCase(unittest.TestCase, cache_api_test.CacheApiTest):
    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_memcache_stub()
        self.setUpCache(memcache_api.MemcacheApi())

    def tearDown(self):
        ndb.get_context().clear_cache()  # Ensure data is truly flushed from memcache
        self.testbed.deactivate()
