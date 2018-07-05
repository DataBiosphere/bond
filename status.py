from google.appengine.api import memcache

class Status:
    def __init__(self, fence_api, sam_api):
        self.fence_api = fence_api
        self.sam_api = sam_api

    def get(self):
        """
        gets status of all sub systems
        :return: dict with key the name of the subsystem, value is a dict with entries "ok": boolean and "message": string
        """
        try:
            status = self._get_cached_status()
            if status:
                return status
            else:
                # if we got this far memcache is ok
                fence_ok, fence_message = self.fence_api.status()
                datastore_ok, datastore_message = self._datastore_status()
                sam_ok, sam_message = self.sam_api.status()

                status = {
                    Subsystems.memcache: {"ok": True, "message": ""},
                    Subsystems.datastore: {"ok": datastore_ok, "message": datastore_message},
                    Subsystems.fence: {"ok": fence_ok, "message": fence_message},
                    Subsystems.sam: {"ok": sam_ok, "message": sam_message}
                }
                self._cache_status(status)
            return status
        except Exception as e:
            # any exception at this point is memcache
            return {
                Subsystems.memcache: {"ok": False, "message": e.message},
                Subsystems.datastore: {"ok": False, "message": "unknown"},
                Subsystems.fence: {"ok": False, "message": "unknown"},
                Subsystems.sam: {"ok": False, "message": "unknown"}
            }

    @staticmethod
    def _cache_status(status):
        memcache.add(namespace='bond', key="status", value=status, time=60)

    @staticmethod
    def _get_cached_status():
        return memcache.get(namespace='bond', key="status")

    @staticmethod
    def _datastore_status():
        try:
            from google.appengine.ext.ndb import stats
            stats.GlobalStat.query().get()
            return True, ""
        except Exception as e:
            return False, e.message


class Subsystems:
    memcache = "memcache"
    datastore = "datastore"
    sam = "sam"
    fence = "fence"
