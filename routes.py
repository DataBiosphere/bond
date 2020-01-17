from flask import Blueprint, request
import ConfigParser
from werkzeug import exceptions

from protorpc import message_types
from protorpc import messages
from protorpc import protojson

import authentication
from bond import Bond
from fence_token_vending import FenceTokenVendingMachine
from fence_api import FenceApi
from open_id_config import OpenIdConfig
from sam_api import SamApi
from oauth_adapter import OauthAdapter
from status import Status
import json
import ast

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

def __init__(self):
    self.auth = authentication.Authentication(authentication.default_config())


config = ConfigParser.ConfigParser()
config.read("config.ini")


def create_provider(provider_name):
    client_id = config.get(provider_name, 'CLIENT_ID')
    client_secret = config.get(provider_name, 'CLIENT_SECRET')
    open_id_config_url = config.get(provider_name, 'OPEN_ID_CONFIG_URL')
    fence_base_url = config.get(provider_name, 'FENCE_BASE_URL')
    user_name_path_expr = config.get(provider_name, 'USER_NAME_PATH_EXPR')

    sam_base_url = config.get('sam', 'BASE_URL')

    extra_authz_url_params = {}
    extra_params_key = 'EXTRA_AUTHZ_URL_PARAMS'
    if config.has_option(provider_name, extra_params_key):
        extra_params_raw = config.get(provider_name, extra_params_key)
        extra_authz_url_params = ast.literal_eval(extra_params_raw)

    open_id_config = OpenIdConfig(provider_name, open_id_config_url)
    oauth_adapter = OauthAdapter(client_id, client_secret, open_id_config, provider_name)
    fence_api = FenceApi(fence_base_url)
    sam_api = SamApi(sam_base_url)

    fence_tvm = FenceTokenVendingMachine(fence_api, sam_api, oauth_adapter, provider_name)
    return BondProvider(fence_tvm, Bond(oauth_adapter,
                                        fence_api,
                                        sam_api,
                                        fence_tvm,
                                        provider_name,
                                        user_name_path_expr,

                                        extra_authz_url_params))


def _get_provider(provider_name):
    if provider_name in bond_providers:
        return bond_providers[provider_name]
    else:
        raise exceptions.NotFound("provider {} not found".format(provider_name))


class BondProvider:
    def __init__(self, fence_tvm, bond):
        self.fence_tvm = fence_tvm
        self.bond = bond


routes = Blueprint('bond', __name__, '/')

bond_providers = {provider_name: create_provider(provider_name)
                  for provider_name in config.sections() if provider_name != 'sam'}

api_routes_base = '/api/link/v1'
@routes.route(api_routes_base + '/providers', methods=["GET"])
def list_providers():
    return protojson.encode_message(ListProvidersResponse(providers=list(bond_providers.keys())))


@routes.route('/api/link/v1/<provider>/oauthcode', methods=["POST"])
def oauthcode(self, provider):
    user_info = self.auth.require_user_info(request)
    issued_at, username = _get_provider(provider).bond.exchange_authz_code(request.args.get('oauthcode'), request.args.get('redirect_uri'), user_info)
    return protojson.encode_message(LinkInfoResponse(issued_at=issued_at, username=username))


@routes.route('/api/link/v1/<provider>', methods=["GET"])
def link_info(self, provider):
    user_info = self.auth.require_user_info(request)
    refresh_token = _get_provider(provider).bond.get_link_info(user_info)
    if refresh_token:
        return protojson.encode_message(LinkInfoResponse(issued_at=refresh_token.issued_at, username=refresh_token.username))
    else:
        raise exceptions.NotFound("{} link does not exist".format(provider))


@routes.route('/api/link/v1/<provider>', methods=["DELETE"])
def delete_link(self, provider):
    user_info = self.auth.require_user_info(request)
    _get_provider(provider).bond.unlink_account(user_info)
    return protojson.encode_message(message_types.VoidMessage())


@routes.route('/api/link/v1/<provider>/accesstoken', methods=["GET"])
def accesstoken(self, provider):
    user_info = self.auth.require_user_info(request)
    try:
        access_token, expires_at = _get_provider(provider).bond.generate_access_token(user_info)
        return protojson.encode_message(AccessTokenResponse(token=access_token, expires_at=expires_at))
    except Bond.MissingTokenError as err:
        # TODO: I don't like throwing and rethrowing exceptions
        raise exceptions.BadRequest(err.message)


@routes.route('/api/link/v1/<provider>/serviceaccount/key', methods=["GET"])
def service_account_key(self, provider):
    user_info = self.auth.require_user_info(request)
    return protojson.encode_message(ServiceAccountKeyResponse(data=json.loads(
        _get_provider(provider).fence_tvm.get_service_account_key_json(user_info))))


@routes.route('/api/link/v1/<provider>/serviceaccount/accesstoken', methods=["GET"])
def service_account_accesstoken(self, provider):
    user_info = self.auth.require_user_info(request)
    return protojson.encode_message(ServiceAccountAccessTokenResponse(token=_get_provider(provider).fence_tvm.get_service_account_access_token(user_info, request.args.getlist('scopes'))))


@routes.route('/api/link/v1/<string:provider>/authorization-url', methods=["GET"])
def authorization_url(provider):
    print("1##########")
    print(type(provider))
    authz_url = _get_provider(provider).bond.build_authz_url(request.args.getlist('scopes'), request.args.get('redirect_uri'), request.args.get('state'))
    return protojson.encode_message((AuthorizationUrlResponse(url=authz_url)))


@routes.route('/api/status/v1/status', methods=["GET"])
def get_status():
    sam_base_url = config.get('sam', 'BASE_URL')

    providers = {provider_name: FenceApi(config.get(provider_name, 'FENCE_BASE_URL'))
                 for provider_name in config.sections() if provider_name != 'sam'}

    sam_api = SamApi(sam_base_url)
    status_service = Status(sam_api, providers)

    subsystems = status_service.get()
    ok = all(subsystem["ok"] for subsystem in subsystems)
    response = protojson.encode_message(StatusResponse(ok=ok,
                              subsystems=[SubSystemStatusResponse(ok=subsystem["ok"],
                                                                  message=subsystem["message"],
                                                                  subsystem=subsystem["subsystem"])
                                          for subsystem in subsystems]))
    if ok:
        return response
    else:
        raise exceptions.InternalServerError(response)
