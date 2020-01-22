import unittest

import flask
import routes
from protorpc import remote
from protorpc import messages
from protorpc import message_types
from google.appengine.ext import testbed
from google.appengine.ext import ndb


class RoutesTestCase(unittest.TestCase):
    """
    Tests the main Google Endpoints methods
    """

    def setUp(self):
        super(RoutesTestCase, self).setUp()
        self.tb = testbed.Testbed()
        self.tb.setup_env(
            current_version_id='testbed.version',
            bond_accepted_audience_prefixes='a',
            bond_accepted_email_suffixes='foo'
        )
        self.tb.activate()

    def tearDown(self):
        self.tb.deactivate()
        super(RoutesTestCase, self).tearDown()

    def test_nothing(self):
        self.assertTrue(True)

    # def test_api_call(self):
    #     # Test API routes exists. If not exists, it will return 404 error code. As long as it is not 404,
    #     # that means the API do exist
    #     app = flask.Flask(__name__)
    #     app.register_blueprint(routes.routes)
    #     app.testing = True
    #
    #     with app.test_client() as c:
    #
    #         response = c.get('/api/does/not/exist')
    #         self.assertEquals(response.status_code, 404)
    #
    #         response = c.get('/api/status/v1/status')
    #         self.assertEquals(response.status_code, 500)
    #
    #         response = c.get('/api/link/v1/providers')
    #         self.assertEquals(response.status_code, 200)
    #
    #         response = c.get('/api/link/v1/foo')
    #         self.assertEquals(response.status_code, 401)


