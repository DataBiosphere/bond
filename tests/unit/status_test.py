import unittest
from tests.unit.fake_cache_api import FakeCacheApi
from bond_app.fence_api import FenceApi
from bond_app.sam_api import SamApi
from mock import MagicMock
from bond_app.status import Status, Subsystems


class StatusTestCase(unittest.TestCase):
    def setUp(self):
        self.cache_api = FakeCacheApi()

    def test_ok_status(self):
        status = Status(self._mock_sam_api(True), {"fence": self._mock_fence_api(True)}, self.cache_api)
        self._mock_datastore(status, True)
        self.assertEqual(len(status.get()), 4)
        self.assertTrue(all(subsystem["ok"] for subsystem in status.get()))

    def test_cache_error(self):
        status = Status(self._mock_sam_api(True), {"fence": self._mock_fence_api(True)}, self.cache_api)
        self._mock_datastore(status, True)
        message = "cache down"
        status._get_cached_status = MagicMock(side_effect=Exception(message))
        self.assertEqual(status.get(), [{"ok": False, "message": message, "subsystem": Subsystems.cache}])

    def test_datastore_error(self):
        status = Status(self._mock_sam_api(True), {"fence": self._mock_fence_api(True)}, self.cache_api)
        self._mock_datastore(status, False)
        self.assertCountEqual(status.get(), [
            {"ok": True, "message": "", "subsystem": Subsystems.cache},
            {"ok": False, "message": "datastore down", "subsystem": Subsystems.datastore},
            {"ok": True, "message": "", "subsystem": "fence"},
            {"ok": True, "message": "", "subsystem": Subsystems.sam},
        ])

    def test_fence_error(self):
        status = Status(self._mock_sam_api(True), {"fence": self._mock_fence_api(False)}, self.cache_api)
        self._mock_datastore(status, True)
        self.assertCountEqual(status.get(), [
            {"ok": True, "message": "", "subsystem": Subsystems.cache},
            {"ok": True, "message": "", "subsystem": Subsystems.datastore},
            {"ok": False, "message": "fence down", "subsystem": "fence"},
            {"ok": True, "message": "", "subsystem": Subsystems.sam},
        ])

    def test_sam_error(self):
        status = Status(self._mock_sam_api(False), {"fence": self._mock_fence_api(True)}, self.cache_api)
        self._mock_datastore(status, True)
        self.assertCountEqual(status.get(), [
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

    @staticmethod
    def _mock_datastore(status, ok):
        if ok:
            status._datastore_status = MagicMock(return_value=(True, ""))
        else:
            status._datastore_status = MagicMock(return_value=(False, "datastore down"))