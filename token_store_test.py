import unittest
import json

# Imports might be highlighted as "unused" by IntelliJ, but they are used, see setUp()
from google.appengine.api import datastore
from google.appengine.api import memcache
from google.appengine.ext import testbed
from google.appengine.ext import ndb
from token_store import TokenStore
from bond_token import BondToken


class TokenStoreTestCase(unittest.TestCase):

    def setUp(self):
        # First, create an instance of the Testbed class.
        self.testbed = testbed.Testbed()
        # Then activate the testbed, which prepares the service stubs for use.
        self.testbed.activate()
        # Next, declare which service stubs you want to use.
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()

        self.some_dict = {"access_token": "foo", "refresh_token": "bar", "token_type": "baz"}
        self.email = "fake@fake.gov"
        self.key = ndb.Key('BondToken', self.email)

    def tearDown(self):
        self.testbed.deactivate()

    def test_save(self):
        self.assertIsNone(self.key.get())
        self.assertEqual(TokenStore.save(self.email, self.some_dict), self.key)
        self.assertIsNotNone(self.key.get())

    def test_lookup(self):
        BondToken(token_dict_str=json.dumps(self.some_dict), id=self.email).put()
        self.assertEqual(TokenStore.lookup(self.email).token_dict(), self.some_dict)
