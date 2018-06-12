import unittest
from refresh_token import RefreshToken


class RefreshTokenTestCase(unittest.TestCase):

    def test_kind_name(self):
        self.assertEqual("RefreshToken", RefreshToken.kind_name())
