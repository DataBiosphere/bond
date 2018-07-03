import ConfigParser
import unittest
# import endpoints
#
# from protorpc import remote
# from protorpc import messages
# from protorpc import message_types
from google.appengine.ext import testbed
# from google.appengine.ext import ndb
from oauth_adapter import OauthAdapter


class OauthAdapterTestCase(unittest.TestCase):

    def setUp(self):
        super(OauthAdapterTestCase, self).setUp()
        self.tb = testbed.Testbed()
        self.tb.activate()
        config = ConfigParser.ConfigParser()
        config.read("config.ini")
        self.client_id = config.get('fence', 'CLIENT_ID')
        self.client_secret = config.get('fence', 'CLIENT_SECRET')
        self.redirect_uri = config.get('fence', 'REDIRECT_URI')
        self.token_url = config.get('fence', 'TOKEN_URL')

    def tearDown(self):
        self.tb.deactivate()
        super(OauthAdapterTestCase, self).tearDown()

    # def test_exchange_authz_code(self):
    #     oauth = OauthAdapter(self.client_id, self.client_secret, self.redirect_uri, self.token_url)
    #     token = oauth.exchange_authz_code(r"xxxxxxx")
    #     expected_keys = ['access_token', 'refresh_token']
    #     self.assertTrue(all(key in expected_keys for key in token.keys()))
