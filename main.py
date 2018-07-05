import ConfigParser
from datetime import datetime

import endpoints
from protorpc import message_types
from protorpc import messages
from protorpc import remote

import authentication
from bond import Bond
from fence_token_vending import FenceTokenVendingMachine
from fence_api import FenceApi
from sam_api import SamApi
from oauth_adapter import OauthAdapter
from status import Status
import json
from status import Subsystems


class JsonField(messages.StringField):
    type = dict


class LinkInfoResponse(messages.Message):
    issued_at = message_types.DateTimeField(1)
    username = messages.StringField(2)


class AccessTokenResponse(messages.Message):
    token = messages.StringField(1)
    expires_at = message_types.DateTimeField(2)


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
    sam = messages.MessageField(SubSystemStatusResponse, 5)


OAUTH_CODE_RESOURCE = endpoints.ResourceContainer(oauthcode=messages.StringField(1, required=True))

SCOPES_RESOURCE = endpoints.ResourceContainer(scopes=messages.StringField(1, repeated=True))

config = ConfigParser.ConfigParser()
config.read("config.ini")

@endpoints.api(name='link', version='v1', base_path="/api/")
class BondApi(remote.Service):
    def __init__(self):
        client_id = config.get('fence', 'CLIENT_ID')
        client_secret = config.get('fence', 'CLIENT_SECRET')
        redirect_uri = config.get('fence', 'REDIRECT_URI')
        token_url = config.get('fence', 'TOKEN_URL')
        fence_base_url = config.get('fence', 'FENCE_BASE_URL')
        sam_base_url = config.get('sam', 'BASE_URL')

        oauth_adapter = OauthAdapter(client_id, client_secret, redirect_uri, token_url)
        fence_api = FenceApi(fence_base_url)
        sam_api = SamApi(sam_base_url)

        self.auth = authentication.Authentication(authentication.default_config())
        self.fence_tvm = FenceTokenVendingMachine(fence_api, sam_api, oauth_adapter)
        self.bond = Bond(oauth_adapter, fence_api, sam_api, self.fence_tvm)

    @endpoints.method(
        OAUTH_CODE_RESOURCE,
        LinkInfoResponse,
        path='fence/oauthcode',
        http_method='POST',
        name='fence/oauthcode')
    def oauthcode(self, request):
        user_info = self.auth.require_user_info(self.request_state)
        issued_at, username = self.bond.exchange_authz_code(request.oauthcode, user_info)
        return LinkInfoResponse(issued_at=issued_at, username=username)

    @endpoints.method(
        message_types.VoidMessage,
        LinkInfoResponse,
        path='fence',
        http_method='GET',
        name='fence link info')
    def link_info(self, request):
        user_info = self.auth.require_user_info(self.request_state)
        refresh_token = self.bond.get_link_info(user_info)
        if refresh_token:
            return LinkInfoResponse(issued_at=refresh_token.issued_at, username=refresh_token.username)
        else:
            raise endpoints.NotFoundException

    @endpoints.method(
        message_types.VoidMessage,
        message_types.VoidMessage,
        path='fence',
        http_method='DELETE',
        name='delete fence link')
    def delete_link(self, request):
        user_info = self.auth.require_user_info(self.request_state)
        self.bond.unlink_account(user_info)
        return message_types.VoidMessage()

    @endpoints.method(
        message_types.VoidMessage,
        AccessTokenResponse,
        path='fence/accesstoken',
        http_method='GET',
        name='get fence accesstoken')
    def accesstoken(self, request):
        user_info = self.auth.require_user_info(self.request_state)
        try:
            access_token, expires_at = self.bond.generate_access_token(user_info)
            return AccessTokenResponse(token=access_token, expires_at=expires_at)
        except Bond.MissingTokenError as err:
            # TODO: I don't like throwing and rethrowing exceptions
            raise endpoints.BadRequestException(err.message)

    @endpoints.method(
        message_types.VoidMessage,
        ServiceAccountKeyResponse,
        path='fence/serviceaccount/key',
        http_method='GET',
        name='get fence service account key')
    def service_account_key(self, request):
        user_info = self.auth.require_user_info(self.request_state)
        return ServiceAccountKeyResponse(data=json.loads(self.fence_tvm.get_service_account_key_json(user_info)))

    @endpoints.method(
        SCOPES_RESOURCE,
        ServiceAccountAccessTokenResponse,
        path='fence/serviceaccount/accesstoken',
        http_method='GET',
        name='get fence service account access token')
    def service_account_accesstoken(self, request):
        user_info = self.auth.require_user_info(self.request_state)
        return ServiceAccountAccessTokenResponse(token=self.fence_tvm.get_service_account_access_token(user_info, request.scopes))


@endpoints.api(name='status', version='v1', base_path="/api/")
class BondStatusApi(remote.Service):
    def __init__(self):
        fence_base_url = config.get('fence', 'FENCE_BASE_URL')
        sam_base_url = config.get('sam', 'BASE_URL')

        fence_api = FenceApi(fence_base_url)
        sam_api = SamApi(sam_base_url)
        self.status_service = Status(fence_api, sam_api)

    @endpoints.method(
        message_types.VoidMessage,
        StatusResponse,
        path='/',
        http_method='GET',
        name='status')
    def status(self, request):
        subsystems = self.status_service.get()
        ok = all(subsystem["ok"] for subsystem in subsystems.values())
        response = StatusResponse(ok=ok,
                                  memcache=SubSystemStatusResponse(ok=subsystems[Subsystems.memcache]["ok"], message=subsystems[Subsystems.memcache]["message"]),
                                  datastore=SubSystemStatusResponse(ok=subsystems[Subsystems.datastore]["ok"], message=subsystems[Subsystems.datastore]["message"]),
                                  fence=SubSystemStatusResponse(ok=subsystems[Subsystems.fence]["ok"], message=subsystems[Subsystems.fence]["message"]),
                                  sam=SubSystemStatusResponse(ok=subsystems[Subsystems.sam]["ok"], message=subsystems[Subsystems.sam]["message"]))
        if ok:
            return response
        else:
            raise endpoints.InternalServerErrorException(response)

api = endpoints.api_server([BondApi, BondStatusApi])
