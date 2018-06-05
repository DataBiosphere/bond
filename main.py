from datetime import datetime

import endpoints
import os
from protorpc import message_types
from protorpc import messages
from protorpc import remote
from requests.auth import HTTPBasicAuth
from requests_oauthlib import OAuth2Session
from requests_toolbelt.adapters import appengine

import authentication

# https://toolbelt.readthedocs.io/en/latest/adapters.html#appengineadapter
appengine.monkeypatch()


class JsonField(messages.StringField):
    type = dict


class LinkInfoResponse(messages.Message):
    expires = message_types.DateTimeField(1)
    username = messages.StringField(2)


class AccessTokenResponse(messages.Message):
    token = messages.StringField(1)


class ServiceAccountKeyResponse(messages.Message):
    data = JsonField(1)  # not quite right as it drops the json under a data element


class ServiceAccountAccessTokenResponse(messages.Message):
    token = messages.StringField(1)


class SubSystemStatusResponse(messages.Message):
    ok = messages.BooleanField(1)
    message = messages.StringField(2)


class StatusResponse(messages.Message):
    ok = messages.BooleanField(1)
    memcache = messages.MessageField(SubSystemStatusResponse, 2)
    datastore = messages.MessageField(SubSystemStatusResponse, 3)
    fence = messages.MessageField(SubSystemStatusResponse, 4)


OAUTH_CODE_RESOURCE = endpoints.ResourceContainer(oauthcode=messages.StringField(1, required=True))

SCOPES_RESOURCE = endpoints.ResourceContainer(scopes=messages.StringField(1, repeated=True))

client_id = os.environ['FENCE_CLIENT_ID']
client_secret = os.environ['FENCE_CLIENT_SECRET']
redirect_uri = os.environ['FENCE_REDIRECT_URI']
fence_token_url = os.environ['FENCE_TOKEN_URL']

# For debugging/testing, you can get a token dict from the oauthcode endpoint and past it in below
# token = {"token_type": "Bearer", "refresh_token": "xxxxxxxx", "access_token": "xxxxxxxxx", "id_token": "xxxxxxxxx", "expires_in": 1200, "expires_at": 1528214759.476306}


@endpoints.api(name='link', version='v1', base_path="/api/")
class BondApi(remote.Service):
    def __init__(self):
        self.auth = authentication.Authentication(authentication.default_config())

    @endpoints.method(
        OAUTH_CODE_RESOURCE,
        AccessTokenResponse,
        path='fence/oauthcode',
        http_method='POST',
        name='fence/oauthcode')
    def oauthcode(self, request):
        user_info = self.auth.require_user_info(self.request_state)
        oauth = OAuth2Session(client_id, redirect_uri=redirect_uri)
        auth = HTTPBasicAuth(client_id, client_secret)
        token_response = oauth.fetch_token(fence_token_url, code=request.oauthcode, auth=auth)
        return AccessTokenResponse(token=token_response.get('access_token'))

    @endpoints.method(
        message_types.VoidMessage,
        LinkInfoResponse,
        path='fence',
        http_method='GET',
        name='fence link info')
    def link_info(self, request):
        user_info = self.auth.require_user_info(self.request_state)
        return LinkInfoResponse(expires=datetime.now(), username="foo")

    @endpoints.method(
        message_types.VoidMessage,
        message_types.VoidMessage,
        path='fence',
        http_method='DELETE',
        name='delete fence link')
    def delete_link(self, request):
        user_info = self.auth.require_user_info(self.request_state)
        return message_types.VoidMessage()

    @endpoints.method(
        message_types.VoidMessage,
        AccessTokenResponse,
        path='fence/accesstoken',
        http_method='GET',
        name='get fence accesstoken')
    def accesstoken(self, request):
        user_info = self.auth.require_user_info(self.request_state)
        # TODO: Token needs to be retrieved from memcache
        oauth = OAuth2Session(client_id, token=token)
        auth = HTTPBasicAuth(client_id, client_secret)
        token_response = oauth.refresh_token(fence_token_url, auth=auth, verify=False)
        return AccessTokenResponse(token=token_response.get("access_token"))

    @endpoints.method(
        message_types.VoidMessage,
        ServiceAccountKeyResponse,
        path='fence/serviceaccount/key',
        http_method='GET',
        name='get fence service account key')
    def service_account_key(self, request):
        user_info = self.auth.require_user_info(self.request_state)
        return ServiceAccountKeyResponse(data={"foo": "bar"})

    @endpoints.method(
        SCOPES_RESOURCE,
        ServiceAccountAccessTokenResponse,
        path='fence/serviceaccount/accesstoken',
        http_method='GET',
        name='get fence service account access token')
    def service_account_accesstoken(self, request):
        user_info = self.auth.require_user_info(self.request_state)
        return ServiceAccountAccessTokenResponse(token="fake SA token " + str(request.scopes))


@endpoints.api(name='status', version='v1', base_path="/api/")
class BondStatusApi(remote.Service):

    @endpoints.method(
        message_types.VoidMessage,
        StatusResponse,
        path='/',
        http_method='GET',
        name='status')
    def status(self, request):
        return StatusResponse(ok=True, memcache=SubSystemStatusResponse(ok=True), datastore=SubSystemStatusResponse(ok=True), fence=SubSystemStatusResponse(ok=True))

api = endpoints.api_server([BondApi, BondStatusApi])
