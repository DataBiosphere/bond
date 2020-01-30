class Status:
    def __init__(self, sam_api, provider_status_apis_by_name, cache_api):
        self.provider_status_apis_by_name = provider_status_apis_by_name
        self.sam_api = sam_api
        self.cache_api = cache_api

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
                    {"ok": True, "message": "", "subsystem": Subsystems.cache},
                    {"ok": datastore_ok, "message": datastore_message, "subsystem": Subsystems.datastore},
                    {"ok": sam_ok, "message": sam_message, "subsystem": Subsystems.sam}
                ]
                self._cache_status(status)
            return status
        except Exception as e:
            # any exception at this point is the cache
            return [{"ok": False, "message": str(e), "subsystem": Subsystems.cache}]

    def _cache_status(self, status):
        self.cache_api.add(namespace='bond', key="status", value=status, expires_in=60)

    def _get_cached_status(self):
        return self.cache_api.get(namespace='bond', key="status")

    @staticmethod
    def _datastore_status():
        try:
            from google.appengine.ext.ndb import stats
            stats.GlobalStat.query().get()
            return True, ""
        except Exception as e:
            return False, e.message


class Subsystems:
    cache = "cache"
    datastore = "datastore"
    sam = "sam"
