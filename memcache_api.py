from google.appengine.api import memcache

from cache_api import CacheApi


class MemcacheApi(CacheApi):
    """
    A wrapper around the memcache library to allow it to be injected as a dependency.

    This allows us to transition to different cache implementations.
    """

    def add(self, key, value, expires_in=0, namespace=None):
        return memcache.add(key=key, value=value, time=expires_in, namespace=namespace)

    def get(self, key, namespace=None):
        return memcache.get(key=key, namespace=namespace)
