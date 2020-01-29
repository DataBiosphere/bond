from collections import namedtuple
import datetime
from fence_token_storage import FenceServiceAccount, _FSA_KEY_LIFETIME

# Internal representation of information being stored about a FenceServiceAccount.
_FenceServiceAccountInfo = namedtuple("_FenceServiceAccountInfo", ["key_json", "expires_at", "update_lock_timeout"])


class FakeFenceTokenStorage:
    """
    An in-memory implementation of the FenceTokenStorage class for use as a fake in testing. Not thread safe, only
    works in a single thread, so does not do real locking.
    """

    def __init__(self):
        # Dict from fsa_keys to FenceServiceAccountInfos.
        self.accounts = {}

    def delete(self, provider_user):
        if provider_user not in self.accounts:
            return None
        account = self.accounts.pop(provider_user)
        return account.key_json

    def retrieve(self, provider_user, prep_key_fn, fence_fetch_fn):
        account_info = None
        if provider_user in self.accounts:
            account_info = self.accounts[provider_user]
        else:
            key_json = fence_fetch_fn(prep_key_fn(provider_user))
            account_info = _FenceServiceAccountInfo(key_json=key_json,
                                                   expires_at=datetime.datetime.now() + _FSA_KEY_LIFETIME,
                                                   update_lock_timeout=None)
            self.accounts[provider_user] = account_info

        return (account_info.key_json, account_info.expires_at)
