import configparser
from requests_oauthlib import OAuth2Session
import requests
import json

config = configparser.ConfigParser()
config.read("config.ini")

provider = 'fence'
client_id = config.get(provider, 'CLIENT_ID')
client_secret = config.get(provider, 'CLIENT_SECRET')
redirect_uri = "http://local.broadinstitute.org/#fence-callback"
open_id_config_url = config.get(provider, 'OPEN_ID_CONFIG_URL')


def auth_code_with_basic_auth():
    fence_authorize_url = requests.get(open_id_config_url).json()["authorization_endpoint"]
    oauth = OAuth2Session(client_id, redirect_uri=redirect_uri, scope=['openid', 'google_credentials'])
    authorization_url, state = oauth.authorization_url(fence_authorize_url)
    return authorization_url


url = auth_code_with_basic_auth()
print(('Please go to %s and authorize access.' % url))
