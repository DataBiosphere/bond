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


class ListProvidersResponse(messages.Message):
    providers = messages.StringField(1, repeated=True)


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
    subsystem = messages.StringField(3)


class StatusResponse(messages.Message):
    ok = messages.BooleanField(1)
    subsystems = messages.MessageField(SubSystemStatusResponse, 2, repeated=True)


class AuthorizationUrlResponse(messages.Message):
    url = messages.StringField(1)


OAUTH_CODE_RESOURCE = endpoints.ResourceContainer(provider=messages.StringField(1),
                                                  oauthcode=messages.StringField(2, required=True),
                                                  redirect_uri=messages.StringField(3, required=True))

SCOPES_RESOURCE = endpoints.ResourceContainer(provider=messages.StringField(1),
                                              scopes=messages.StringField(2, repeated=True))

AUTHZ_URL_RESOURCE = endpoints.ResourceContainer(provider=messages.StringField(1),
                                                 scopes=messages.StringField(2, repeated=True),
                                                 redirect_uri=messages.StringField(3, required=True),
                                                 state=messages.StringField(4))

PROVIDER_RESOURCE = endpoints.ResourceContainer(provider=messages.StringField(1))

config = ConfigParser.ConfigParser()
config.read("config.ini")


class BondProvider:
    def __init__(self, fence_tvm, bond):
        self.fence_tvm = fence_tvm
        self.bond = bond


@endpoints.api(name='link', version='v1', base_path="/api/")
class BondApi(remote.Service):
    def __init__(self):
        def create_provider(provider_name):
            client_id = config.get(provider_name, 'CLIENT_ID')
            client_secret = config.get(provider_name, 'CLIENT_SECRET')
            open_id_config_url = config.get(provider_name, 'OPEN_ID_CONFIG_URL')
            fence_base_url = config.get(provider_name, 'FENCE_BASE_URL')
            user_name_path_expr = config.get(provider_name, 'USER_NAME_PATH_EXPR')

            sam_base_url = config.get('sam', 'BASE_URL')
    
            oauth_adapter = OauthAdapter(client_id, client_secret, open_id_config_url, provider_name)
            fence_api = FenceApi(fence_base_url)
            sam_api = SamApi(sam_base_url)

            fence_tvm = FenceTokenVendingMachine(fence_api, sam_api, oauth_adapter, provider_name)
            return BondProvider(fence_tvm, Bond(oauth_adapter, fence_api, sam_api, fence_tvm, provider_name, user_name_path_expr))

        self.providers = {provider_name: create_provider(provider_name) 
                          for provider_name in config.sections() if provider_name != 'sam'}
        self.auth = authentication.Authentication(authentication.default_config())

    def _get_provider(self, provider_name):
        if provider_name in self.providers:
            return self.providers[provider_name]
        else:
            raise endpoints.NotFoundException("provider {} not found".format(provider_name))

    @endpoints.method(
        message_types.VoidMessage,
        ListProvidersResponse,
        path='/providers',
        http_method='GET',
        name='listProviders')
    def providers(self, request):
        return ListProvidersResponse(providers=self.providers.keys())

    @endpoints.method(
        OAUTH_CODE_RESOURCE,
        LinkInfoResponse,
        path='{provider}/oauthcode',
        http_method='POST',
        name='oauthcode')
    def oauthcode(self, request):
        user_info = self.auth.require_user_info(self.request_state)
        issued_at, username = self._get_provider(request.provider).bond.exchange_authz_code(request.oauthcode, request.redirect_uri, user_info)
        return LinkInfoResponse(issued_at=issued_at, username=username)

    @endpoints.method(
        PROVIDER_RESOURCE,
        LinkInfoResponse,
        path='{provider}',
        http_method='GET',
        name='getLinkInfo')
    def link_info(self, request):
        user_info = self.auth.require_user_info(self.request_state)
        refresh_token = self._get_provider(request.provider).bond.get_link_info(user_info)
        if refresh_token:
            return LinkInfoResponse(issued_at=refresh_token.issued_at, username=refresh_token.username)
        else:
            raise endpoints.NotFoundException("{} link does not exist".format(request.provider))

    @endpoints.method(
        PROVIDER_RESOURCE,
        message_types.VoidMessage,
        path='{provider}',
        http_method='DELETE',
        name='revokeLink')
    def delete_link(self, request):
        user_info = self.auth.require_user_info(self.request_state)
        self._get_provider(request.provider).bond.unlink_account(user_info)
        return message_types.VoidMessage()

    @endpoints.method(
        PROVIDER_RESOURCE,
        AccessTokenResponse,
        path='{provider}/accesstoken',
        http_method='GET',
        name='getAccessToken')
    def accesstoken(self, request):
        user_info = self.auth.require_user_info(self.request_state)
        try:
            access_token, expires_at = self._get_provider(request.provider).bond.generate_access_token(user_info)
            return AccessTokenResponse(token=access_token, expires_at=expires_at)
        except Bond.MissingTokenError as err:
            # TODO: I don't like throwing and rethrowing exceptions
            raise endpoints.BadRequestException(err.message)

    @endpoints.method(
        PROVIDER_RESOURCE,
        ServiceAccountKeyResponse,
        path='{provider}/serviceaccount/key',
        http_method='GET',
        name='getServiceAccountKey')
    def service_account_key(self, request):
        user_info = self.auth.require_user_info(self.request_state)
        return ServiceAccountKeyResponse(data=json.loads(
            self._get_provider(request.provider).fence_tvm.get_service_account_key_json(user_info)))

    @endpoints.method(
        SCOPES_RESOURCE,
        ServiceAccountAccessTokenResponse,
        path='{provider}/serviceaccount/accesstoken',
        http_method='GET',
        name='getServiceAccountAccessToken')
    def service_account_accesstoken(self, request):
        user_info = self.auth.require_user_info(self.request_state)
        return ServiceAccountAccessTokenResponse(token=self._get_provider(request.provider).fence_tvm.get_service_account_access_token(user_info, request.scopes))

    @endpoints.method(
        AUTHZ_URL_RESOURCE,
        AuthorizationUrlResponse,
        path='{provider}/authorization-url',
        http_method='GET',
        name='getAuthorizationUrl')
    def authorization_url(self, request):
        authz_url = self._get_provider(request.provider).bond.build_authz_url(request.scopes,
                                                                         request.redirect_uri,
                                                                         request.state)
        return AuthorizationUrlResponse(url=authz_url)


@endpoints.api(name='status', version='v1', base_path="/api/")
class BondStatusApi(remote.Service):
    def __init__(self):
        sam_base_url = config.get('sam', 'BASE_URL')

        providers = {provider_name: FenceApi(config.get(provider_name, 'FENCE_BASE_URL'))
                     for provider_name in config.sections() if provider_name != 'sam'}

        sam_api = SamApi(sam_base_url)
        self.status_service = Status(sam_api, providers)

    @endpoints.method(
        message_types.VoidMessage,
        StatusResponse,
        path='/status',
        http_method='GET',
        name='status')
    def status(self, request):
        subsystems = self.status_service.get()
        ok = all(subsystem["ok"] for subsystem in subsystems)
        response = StatusResponse(ok=ok,
                                  subsystems=[SubSystemStatusResponse(ok=subsystem["ok"],
                                                                      message=subsystem["message"],
                                                                      subsystem=subsystem["subsystem"])
                                              for subsystem in subsystems])
        if ok:
            return response
        else:
            raise endpoints.InternalServerErrorException(response)

api = endpoints.api_server([BondApi, BondStatusApi])
