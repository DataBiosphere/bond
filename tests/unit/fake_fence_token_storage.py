import datetime
from fence_token_storage import FenceServiceAccount, _FSA_KEY_LIFETIME


class FakeFenceTokenStorage:
    """
    An in-memory implementation of the FenceTokenStorage class for use as a fake in testing. Not thread safe, only
    works in a single thread, so does not do real locking.
    """

    def __init__(self):
        # Dict from fsa_keys to FenceServiceAccounts.
        self.accounts = {}

    def delete(self, fsa_key):
        if fsa_key not in self.accounts:
            return None
        account = self.accounts.pop(fsa_key)
        return account.json_key

    def get_or_create(self, fsa_key, prep_key_fn, create_value_fn):
        if fsa_key in self.accounts:
            return self.accounts[fsa_key]

        json_key = self.create_value_fn(self.prep_key_fn(fsa_key))
        fence_service_account = FenceServiceAccount(key_json=json_key,
                                                    expires_at=datetime.datetime.now() + _FSA_KEY_LIFETIME,
                                                    update_lock_timeout=None,
                                                    key=fsa_key)
        self.accounts[fsa_key] = fence_service_account
        return fence_service_account
