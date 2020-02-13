import time

from bond_app.cache_api import CacheApi


class FakeCacheApi(CacheApi):
    """An implementation of CacheApi for testing using in memory dicts."""

    class TimedValue:
        """An added value and its expiration time in seconds since Unix epoch."""
        def __init__(self, value, expires_in):
            """
            :param value: the added values.
            :param expires_in: The number of seconds to allow this value before expiring.
            """
            self.value = value
            self.expiration_time = None if expires_in == 0 else time.time() + expires_in

        def get_valid_value(self):
            """Returns the value if it has not expired, otherwise None. """
            return self.value if not self.expiration_time or time.time() < self.expiration_time else None


    def __init__(self):
        # Dict for keys with no namespace. Stores TimedValues.
        self.cache = {}
        # Dict from namespace to dicts of keys to TimedValues.
        self.namespaces = {}

    def add(self, key, value, expires_in=0, namespace=None):
        timed_value = FakeCacheApi.TimedValue(value, expires_in)
        if namespace:
            namespace_dict = self.namespaces.setdefault(namespace, {})
            namespace_dict[key] = timed_value
        else:
            self.cache[key] = timed_value
        return True

    def get(self, key, namespace=None):
        timed_value = None
        if namespace:
            namespace_dict = self.namespaces.get(namespace)
            if not namespace_dict:
                return None
            timed_value = namespace_dict.get(key)
        else:
            timed_value = self.cache.get(key)
        return timed_value.get_valid_value() if timed_value else None