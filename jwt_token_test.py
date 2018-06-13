import unittest
import jwt
from jwt_token import JwtToken


class JwtTokenTestCase(unittest.TestCase):

    def test_init(self):
        name = "Bob McBob"
        data = {"context": {"user": {"name": name}}}
        encoded = jwt.encode(data, 'secret', 'HS256')
        jwt_token = JwtToken(encoded)
        self.assertEqual(name, jwt_token.username)
