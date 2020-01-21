import unittest
from tests.unit.fake_cache_api import FakeCacheApi
from fence_api import FenceApi
from sam_api import SamApi
from mock import MagicMock
from status import Status, Subsystems
from google.appengine.ext import testbed
from google.appengine.ext import ndb


class StatusTestCase(unittest.TestCase):
    def setUp(self):
        # First, create an instance of the Testbed class.
        self.testbed = testbed.Testbed()
        # Then activate the testbed, which prepares the service stubs for use.
        self.testbed.activate()
        # Next, declare which service stubs you want to use.
        self.testbed.init_datastore_v3_stub()

        self.cache_api = FakeCacheApi()

    def tearDown(self):
        ndb.get_context().clear_cache()  # Ensure data is truly flushed from datastore
        self.testbed.deactivate()

    def test_ok_status(self):
        status = Status(self._mock_sam_api(True), {"fence": self._mock_fence_api(True)}, self.cache_api)
        self.assertEqual(len(status.get()), 4)
        self.assertTrue(all(subsystem["ok"] for subsystem in status.get()))

    def test_cache_error(self):
        status = Status(self._mock_sam_api(True), {"fence": self._mock_fence_api(True)}, self.cache_api)
        message = "cache down"
        status._get_cached_status = MagicMock(side_effect=Exception(message))
        self.assertEqual(status.get(), [{"ok": False, "message": message, "subsystem": Subsystems.cache}])

    def test_datastore_error(self):
        status = Status(self._mock_sam_api(True), {"fence": self._mock_fence_api(True)}, self.cache_api)
        status._datastore_status = MagicMock(return_value=(False, "datastore down"))
        self.assertItemsEqual(status.get(), [
            {"ok": True, "message": "", "subsystem": Subsystems.cache},
            {"ok": False, "message": "datastore down", "subsystem": Subsystems.datastore},
            {"ok": True, "message": "", "subsystem": "fence"},
            {"ok": True, "message": "", "subsystem": Subsystems.sam},
        ])

    def test_fence_error(self):
        status = Status(self._mock_sam_api(True), {"fence": self._mock_fence_api(False)}, self.cache_api)
        self.assertItemsEqual(status.get(), [
            {"ok": True, "message": "", "subsystem": Subsystems.cache},
            {"ok": True, "message": "", "subsystem": Subsystems.datastore},
            {"ok": False, "message": "fence down", "subsystem": "fence"},
            {"ok": True, "message": "", "subsystem": Subsystems.sam},
        ])

    def test_sam_error(self):
        status = Status(self._mock_sam_api(False), {"fence": self._mock_fence_api(True)}, self.cache_api)
        self.assertItemsEqual(status.get(), [
            {"ok": True, "message": "", "subsystem": Subsystems.cache},
            {"ok": True, "message": "", "subsystem": Subsystems.datastore},
            {"ok": True, "message": "", "subsystem": "fence"},
            {"ok": False, "message": "sam down", "subsystem": Subsystems.sam},
        ])

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
            sam_api.status = MagicMock(return_value=(True, ""))
        else:
            sam_api.status = MagicMock(return_value=(False, "sam down"))
        return sam_api
