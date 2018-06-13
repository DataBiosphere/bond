import unittest
from refresh_token import RefreshToken
from datetime import datetime


class RefreshTokenTestCase(unittest.TestCase):

    def test_kind_name(self):
        self.assertEqual("RefreshToken", RefreshToken.kind_name())

    def test_properties(self):
        user_id = "bob"
        token_str = "foobarbaz"
        issued_at = datetime.now()
        refresh_token = RefreshToken(id=user_id, token=token_str, issued_at=issued_at)
        self.assertEqual(user_id, refresh_token.key.id())
        self.assertEqual(token_str, refresh_token.token)
        self.assertEqual(issued_at, refresh_token.issued_at)
