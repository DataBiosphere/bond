from dataclasses import dataclass
from datetime import datetime

from google.cloud import ndb


# Information associated with a tokens for refreshing service account credentials.
@dataclass
class RefreshTokenInfo:
    token: str
    issued_at: datetime
    username: str


class RefreshToken(ndb.Model):
    """
    Model used to store entries in Datastore.

    This is not used as the return type for TokenStore because it depends on ndb, which we want to stub out for unit
    tests.
    """
    token = ndb.TextProperty(exclude_from_indexes=True)
    issued_at = ndb.DateTimeProperty()
    username = ndb.StringProperty()

    @classmethod
    def kind_name(cls):
        return cls.__name__


class TokenStore:
    """
    Stores refresh tokens for service accounts in Datastore.

    TODO Consider renaming this to RefreshTokenStore to distinguish the type of tokens.
    """

    def save(self, user_id, refresh_token_str, issued_at, username, provider_name):
        """
        Persists a RefreshToken by creating a new entity or updating an existing entity with the same id
        :param provider_name:
        :param user_id: identifier for the Google Datastore entity
        :param refresh_token_str: a refresh token string
        :param issued_at: datetime at which the token was issued
        :param username: username for whom the token was issued
        """
        refresh_token = RefreshToken(key=TokenStore._token_store_key(user_id, provider_name),
                                     token=refresh_token_str,
                                     issued_at=issued_at,
                                     username=username)
        refresh_token.put()

    def lookup(self, user_id, provider_name):
        """
        Retrieves an entity out of Google Datastore of the "RefreshToken" type with the specified user_id
        :param provider_name:
        :param user_id: unique identifier for the RefreshToken entity
        :return: A RefreshTokenInfo, or None if not found.
        """
        refresh_token = TokenStore._token_store_key(user_id, provider_name).get()
        if not refresh_token:
            return None
        return RefreshTokenInfo(token=refresh_token.token, issued_at=refresh_token.issued_at,
                                username=refresh_token.username)

    def delete(self, user_id, provider_name):
        TokenStore._token_store_key(user_id, provider_name).delete()

    @staticmethod
    def _token_store_key(user_id, provider_name):
        return ndb.Key("User", user_id, RefreshToken, provider_name)
