class CacheApi:
    def add(self, key, value, expires_in=0, namespace=None):
        """
        Adds the (key, value) to the cache.
        :param key: A string key
        :param value: The value to store, retrieved later with 'get.'
        :param expires_in: The number of seconds to keep the entry before expiration. If zero, never expires.
        :param namespace: An optional string to further divide the key space.
        :return: True if added, False on error.
        """
        raise NotImplementedError

    def get(self, key, namespace=None):
        """
        Retrieves a the value stored by 'add.'
        :param key: A string key.
        :param namespace: The namespace used for the 'add' if any.
        :return: The value of the key if found, else None.
        """
        raise NotImplementedError

def create_cache_api():
    """Create the CacheApi to use in the application."""
    # TODO(CA-648): Implement an alternative to memcache.
    # We import memcache_api locally here so that we do not automatically depend on the memcache library. This will make
    # our migration to python 3, where memcache is not supported.
    import memcache_api
    return memcache_api.MemcacheApi()

