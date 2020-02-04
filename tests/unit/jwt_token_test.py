import unittest
import jwt
from bond_app.jwt_token import JwtToken
from datetime import datetime


class JwtTokenTestCase(unittest.TestCase):

    def test_init(self):
        name = "Bob McBob"
        issued_at = 1528896868
        data = {"context": {"user": {"name": name}}, 'iat': issued_at}
        encoded = jwt.encode(data, 'secret', 'HS256')
        jwt_token = JwtToken(encoded, "/context/user/name")
        self.assertEqual(name, jwt_token.username)
        self.assertEqual(datetime.fromtimestamp(issued_at), jwt_token.issued_at)
