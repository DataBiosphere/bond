from google.appengine.ext import ndb
from bond_token import BondToken
import json


class TokenStore():

    @staticmethod
    def save(email, token_dict):
        """
        Persists a BondToken by creating a new entity or updating an existing entity with the same id
        :param email: identifier for the Google Datastore entity, in our case an email address
        :param token_dict: a dict instance populated with token information
        :return: The datastore Key of the persisted entity
        """
        # TODO: Should we validate the structure of token_dict?  What should these rules be?
        token_entity = BondToken(token_dict=json.dumps(token_dict), id=email)
        return token_entity.put()

    @staticmethod
    def lookup(email):
        """
        Retrieves an entity out of Google Datastore of the "BondToken" type and id (email address)
        :param email: unique identifier (email address) for the BondToken entity
        :return: A dict instance populated with token information
        """
        bond_token = ndb.Key('BondToken', email).get()
        return json.loads(bond_token.token_dict)
