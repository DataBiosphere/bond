from google.appengine.api import memcache

class Status:
    def __init__(self, sam_api, provider_status_apis_by_name):
        self.provider_status_apis_by_name = provider_status_apis_by_name
        self.sam_api = sam_api

    def get(self):
        """
        gets status of all sub systems
        :return: list of dicts with entries "ok": boolean, "message": string, "subsystem": name
        """
        try:
            status = self._get_cached_status()
            if status:
                return status
            else:
                # if we got this far memcache is ok
                provider_statuses = [(provider_name, provider_api.status())
                                     for (provider_name, provider_api) in list(self.provider_status_apis_by_name.items())]
                provider_status_messages = [{"ok": ok, "message": message, "subsystem": provider_name}
                                            for (provider_name, (ok, message)) in provider_statuses]

                datastore_ok, datastore_message = self._datastore_status()
                sam_ok, sam_message = self.sam_api.status()

                status = provider_status_messages + [
                    {"ok": True, "message": "", "subsystem": Subsystems.memcache},
                    {"ok": datastore_ok, "message": datastore_message, "subsystem": Subsystems.datastore},
                    {"ok": sam_ok, "message": sam_message, "subsystem": Subsystems.sam}
                ]
                self._cache_status(status)
            return status
        except Exception as e:
            # any exception at this point is memcache
            return [{"ok": False, "message": e.message, "subsystem": Subsystems.memcache}]

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
