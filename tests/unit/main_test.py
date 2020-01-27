import unittest

from protorpc import remote
from protorpc import messages
from protorpc import message_types
from google.appengine.ext import testbed
from google.appengine.ext import ndb



class MainTestCase(unittest.TestCase):
    """
    Tests the main Google Endpoints methods
    """

    def setUp(self):
        super(MainTestCase, self).setUp()
        self.tb = testbed.Testbed()
        self.tb.setup_env(
            current_version_id='testbed.version',
            bond_accepted_audience_prefixes='a',
            bond_accepted_email_suffixes='foo'
        )
        self.tb.activate()

    def tearDown(self):
        self.tb.deactivate()
        super(MainTestCase, self).tearDown()

    def test_nothing(self):
        self.assertTrue(True)

    # def test_api_call(self):
        # response = self.bond_api.link_info(message_types.VoidMessage)
        # print("\n\nResponse was: {}\n\n".format(response))
