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

    def delete(self, key, namespace=None):
        """
        Deletes the value specified by key
        :param key: A string key
        :param namespace: The namespace used for the 'add' if any.
        :return: None if entry at key was deleted or not found
        """
        raise NotImplementedError
