import time
import unittest

from cache_api import LocalCacheApi


class LocalCacheApiTestCase(unittest.TestCase):

    def test_added_values_retrieved(self):
        cache = LocalCacheApi()
        self.assertTrue(cache.add('foo', 42))
        self.assertTrue(cache.add('bam', 123))
        self.assertTrue(cache.add('bar', 24, namespace='baz'))

        self.assertEquals(cache.get('foo'), 42)
        self.assertEquals(cache.get('bam'), 123)
        self.assertIsNone(cache.get('abc'))
        self.assertIsNone(cache.get('foo', namespace='baz'))

        self.assertEquals(cache.get('bar', namespace='baz'), 24)
        self.assertIsNone(cache.get('bar'))
        self.assertIsNone(cache.get('bar', namespace='qat'))

    def test_expiration(self):
        cache = LocalCacheApi()
        self.assertTrue(cache.add('foo', 42, expires_in=0.5))
        self.assertTrue(cache.add('foo', 24, expires_in=0.5, namespace='bar'))

        self.assertEquals(cache.get('foo'), 42)
        self.assertEquals(cache.get('foo', namespace='bar'), 24)
        time.sleep(1)
        self.assertIsNone(cache.get('foo'))
        self.assertIsNone(cache.get('foo', namespace='bar'))
