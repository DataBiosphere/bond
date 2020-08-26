import time
import unittest

from tests.unit.fake_cache_api import FakeCacheApi


class CacheApiTest(object):
    """
    Base class for testing the CacheApi interface.
    Implementations of CacheApi should subclass this class for testing, calling 'setUpCache' in setUp as needed.
    """

    def setUpCache(self, cache):
        self.cache = cache

    def test_added_values_retrieved(self):
        self.assertIsNone(self.cache.get("foo"))

        self.assertTrue(self.cache.add('foo', 42))
        self.assertTrue(self.cache.add('bam', 123))
        self.assertTrue(self.cache.add('bar', 24, namespace='baz'))

        self.assertEqual(self.cache.get('foo'), 42)
        self.assertEqual(self.cache.get('bam'), 123)
        self.assertIsNone(self.cache.get('abc'))
        self.assertIsNone(self.cache.get('foo', namespace='baz'))

        self.assertEqual(self.cache.get('bar', namespace='baz'), 24)
        self.assertIsNone(self.cache.get('bar'))
        self.assertIsNone(self.cache.get('bar', namespace='qat'))

    def test_expiration(self):
        self.assertIsNone(self.cache.get("foo"))

        self.assertTrue(self.cache.add('foo', 42, expires_in=0.5))
        self.assertTrue(self.cache.add('foo', 24, expires_in=0.5, namespace='bar'))

        self.assertEqual(self.cache.get('foo'), 42)
        self.assertEqual(self.cache.get('foo', namespace='bar'), 24)
        time.sleep(1)
        self.assertIsNone(self.cache.get('foo'))
        self.assertIsNone(self.cache.get('foo', namespace='bar'))

    def test_simple_delete(self):
        self.assertTrue(self.cache.add('foo', 42))
        self.assertEqual(self.cache.get('foo'), 42)
        self.assertIsNone(self.cache.delete('foo'))
        self.assertIsNone(self.cache.get('foo'))

    def test_delete_with_namespace(self):
        self.assertTrue(self.cache.add('bar', 11, namespace='baz'))
        self.assertIsNone(self.cache.get('bar'))
        self.assertEqual(self.cache.get('bar', namespace='baz'), 11)
        self.assertIsNone(self.cache.delete('bar', namespace='baz'))
        self.assertIsNone(self.cache.get('bar', namespace='baz'))

    def test_delete_tolerates_missing_key(self):
        self.assertIsNone(self.cache.delete('foo'))
        self.assertIsNone(self.cache.delete('foo', namespace='bar'))


class FakeCacheApiTestCase(unittest.TestCase, CacheApiTest):
    def setUp(self):
        self.setUpCache(FakeCacheApi())
