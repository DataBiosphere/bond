import unittest

import dpath.exceptions
import jwt
from bond_app.jwt_token import JwtToken
from datetime import datetime


class JwtTokenTestCase(unittest.TestCase):

    def setUp(self):
        self.name = "Bob McBob"
        self.issued_at = 1528896868
        self.data = {"context": {"user": {"name": self.name}}, 'iat': self.issued_at}

    def encoded(self):
        return jwt.encode(self.data, 'secret', 'HS256')

    def jwt_token(self):
        return JwtToken(self.encoded(), "/context/user/name")

    def test_constructor(self):
        bond_jwt_token = self.jwt_token()
        self.assertEqual(self.name, bond_jwt_token.username)
        self.assertEqual(datetime.fromtimestamp(self.issued_at), bond_jwt_token.issued_at)

    def test_jwt_with_empty_key(self):
        self.data[''] = 'dict entry with empty key'
        self.test_constructor()
