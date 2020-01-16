""" Json Schemas for api_test.py """


"""Json Schemas for PublicApiTestCase tests"""
json_schema_test_status = {
    "type": "object",
    "properties": {
        "providers": {
            "type": "array",
            "items": {
                "type": "string",
                "minItems": 2,
                "enum": ["fence", "dcf-fence"]
            }
        }
    },
}
json_schema_test_list_providers = {
  "definitions": {},
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "http://example.com/root.json",
  "type": "object",
  "title": "The Root Schema",
  "required": [
    "ok",
    "subsystems"
  ],
  "properties": {
    "ok": {
      "$id": "#/properties/ok",
      "type": "boolean",
      "title": "The Ok Schema",
      "enum": [True]
    },
    "subsystems": {
      "$id": "#/properties/subsystems",
      "type": "array",
      "title": "The Subsystems Schema",
      "items": {
        "$id": "#/properties/subsystems/items",
        "minItems": 5,
        "type": "object",
        "title": "The Items Schema",
        "required": [
          "message",
          "ok",
          "subsystem"
        ],
        "properties": {
          "message": {
            "$id": "#/properties/subsystems/items/properties/message",
            "type": "string",
            "title": "The Message Schema",
            "default": "",
            "pattern": "^(.*)$"
          },
          "ok": {
            "$id": "#/properties/subsystems/items/properties/ok",
            "type": "boolean",
            "title": "The Ok Schema",
            "enum": [True]  # todo: add comments to these. or to the top description.
          },
          "subsystem": {
            "$id": "#/properties/subsystems/items/properties/subsystem",
            "type": "string",
            "title": "The Subsystem Schema",
            "enum": [
              "fence",
              "dcf-fence",
              "memcache",
              "datastore",
              "sam"
            ],
            "pattern": "^(.*)$"
          }
        }
      }
    }
  }
}

json_schema_test_get_auth_url = {}
json_schema_test_get_auth_url_without_params = {}
json_schema_test_get_auth_url_with_only_redirect_param = {}

"""Json Schemas for UnlinkedUserTestCase tests"""
json_schema_test_delete_link_for_unlinked_user = {}
json_schema_test_get_link_status_for_unlinked_user = {}
json_schema_test_get_link_status_for_invalid_provider = {}
json_schema_test_get_access_token_for_unlinked_user = {}

"""Json Schemas for ExchangeAuthCodeTestCase tests"""
json_schema_test_exchange_auth_code = {}

"""Json Schemas for ExchangeAuthCodeNegativeTestCase tests"""
json_schema_test_exchange_auth_code_without_authz_header = {}
json_schema_test_exchange_auth_code_without_redirect_uri_param = {}
json_schema_test_exchange_auth_code_without_oauthcode_param = {}

"""Json Schemas for LinkedUserTestCase tests"""
json_schema_test_get_link_status = {}
json_schema_test_get_access_token = {}
json_schema_test_get_serviceaccount_key = {}

"""Json Schemas for UnlinkLinkedUserTestCase tests"""
json_schema_test_delete_link_for_linked_user = {}
json_schema_test_delete_link_for_invalid_provider = {}

"""Json Schemas for UserCredentialsTestCase tests"""
json_schema_test_token = {}
json_schema_test_user_info_for_delegated_user = {}