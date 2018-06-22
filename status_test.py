import unittest
from fence_api import FenceApi
from sam_api import SamApi
from mock import MagicMock
from status import Status, Subsystems
from google.appengine.ext import testbed


class StatusTestCase(unittest.TestCase):
    def setUp(self):
        # First, create an instance of the Testbed class.
        self.testbed = testbed.Testbed()
        # Then activate the testbed, which prepares the service stubs for use.
        self.testbed.activate()
        # Next, declare which service stubs you want to use.
        self.testbed.init_memcache_stub()
        self.testbed.init_datastore_v3_stub()

    def test_ok_status(self):
        status = Status(self._mock_fence_api(True), self._mock_sam_api(True))
        print status.get()[Subsystems.memcache]["message"]
        self.assertTrue(status.get()[Subsystems.memcache]["ok"])
        self.assertTrue(status.get()[Subsystems.datastore]["ok"])
        self.assertTrue(status.get()[Subsystems.fence]["ok"])
        self.assertTrue(status.get()[Subsystems.sam]["ok"])

    def test_memcache_error(self):
        status = Status(self._mock_fence_api(True), self._mock_sam_api(True))
        status._get_cached_status = MagicMock(side_effect=Exception("memcache down"))
        self.assertFalse(status.get()[Subsystems.memcache]["ok"])
        self.assertFalse(status.get()[Subsystems.datastore]["ok"])
        self.assertFalse(status.get()[Subsystems.fence]["ok"])
        self.assertFalse(status.get()[Subsystems.sam]["ok"])

    def test_datastore_error(self):
        status = Status(self._mock_fence_api(True), self._mock_sam_api(True))
        status._datastore_status = MagicMock(return_value=(False, "datastore down"))
        self.assertTrue(status.get()[Subsystems.memcache]["ok"])
        self.assertFalse(status.get()[Subsystems.datastore]["ok"])
        self.assertTrue(status.get()[Subsystems.fence]["ok"])
        self.assertTrue(status.get()[Subsystems.sam]["ok"])

    def test_fence_error(self):
        status = Status(self._mock_fence_api(False), self._mock_sam_api(True))
        self.assertTrue(status.get()[Subsystems.memcache]["ok"])
        self.assertTrue(status.get()[Subsystems.datastore]["ok"])
        self.assertFalse(status.get()[Subsystems.fence]["ok"])
        self.assertTrue(status.get()[Subsystems.sam]["ok"])

    def test_sam_error(self):
        status = Status(self._mock_fence_api(True), self._mock_sam_api(False))
        self.assertTrue(status.get()[Subsystems.memcache]["ok"])
        self.assertTrue(status.get()[Subsystems.datastore]["ok"])
        self.assertTrue(status.get()[Subsystems.fence]["ok"])
        self.assertFalse(status.get()[Subsystems.sam]["ok"])

    @staticmethod
    def _mock_fence_api(ok):
        fence_api = FenceApi("")
        if ok:
            fence_api.status = MagicMock(return_value=(True, ""))
        else:
            fence_api.status = MagicMock(return_value=(False, "fence down"))
        return fence_api

    @staticmethod
    def _mock_sam_api(ok):
        sam_api = SamApi("")
        if ok:
            sam_api.status = MagicMock(return_value=(True, "sam down"))
        else:
            sam_api.status = MagicMock(return_value=(False, "sam down"))
        return sam_api
