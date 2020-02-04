from collections import namedtuple
from bond_app.token_store import RefreshTokenInfo

# Internal key class for a user_id and provider_name.
_UserKey = namedtuple("_UserKey", ["user_id", "provider_name"])


class FakeTokenStore():
    """A fake in memory implementation of TokenStore for unit tests."""

    def __init__(self):
        # Map from TokenStore keys to RefreshTokens.
        self.tokens = {}

    def save(self, user_id, refresh_token_str, issued_at, username, provider_name):
        """
        Persists a RefreshToken by creating a new entity or updating an existing entity with the same id
        :param provider_name:
        :param user_id: identifier for the Google Datastore entity
        :param refresh_token_str: a refresh token string
        :param issued_at: datetime at which the token was issued
        :param username: username for whom the token was issued
        """
        key = _UserKey(user_id, provider_name)
        refresh_token = RefreshTokenInfo(token=refresh_token_str, issued_at=issued_at, username=username)
        self.tokens[key] = refresh_token

    def lookup(self, user_id, provider_name):
        """
        Retrieves an entity out of Google Datastore of the "RefreshToken" type with the specified user_id
        :param provider_name:
        :param user_id: unique identifier for the RefreshToken entity
        :return: A RefreshToken entity
        """
        return self.tokens.get(_UserKey(user_id, provider_name))

    def delete(self, user_id, provider_name):
        self.tokens.pop(_UserKey(user_id, provider_name), None)
