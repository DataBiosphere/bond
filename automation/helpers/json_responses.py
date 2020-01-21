"""
Json Schemas for api_test.py

Generate, modify, or validate a schema from json here: https://jsonschema.net/

Use "enum" to ensure exact values.
 """

DATE_REGEX = "20..-..-..T..:..:.."  # valid through 2099

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
            "enum": [True]
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
json_schema_test_get_auth_url = {
  "definitions": {},
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "http://example.com/root.json",
  "type": "object",
  "title": "The Root Schema",
  "required": [
    "url"
  ],
  "properties": {
    "url": {
      "$id": "#/properties/url",
      "type": "string",
      "title": "The Url Schema",
      "default": "",
      "examples": [
        "https://staging.datastage.io/user/oauth2/authorize?response_type=code&client_id=4EmZnWKVMoPyhdJMh7EB8SSl3Uojo20QfsAR77gu&redirect_uri=http%3A%2F%2Flocal.broadinstitute.org%2F%23fence-callback&scope=openid+google_credentials&state=eyJmb28iPSJiYXIifQ%3D%3D&idp=fence"
      ],
      "pattern": "(https)(.*)(response_type)(.*)(client_id)(.*)(redirect_uri)(.*)(state)(.*)"
    }
  }
}
json_schema_test_get_auth_url_without_params = {
  "definitions": {},
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "http://example.com/root.json",
  "type": "object",
  "title": "The Root Schema",
  "required": [
    "error"
  ],
  "properties": {
    "error": {
      "$id": "#/properties/error",
      "type": "object",
      "title": "The Error Schema",
      "required": [
        "code",
        "errors",
        "message"
      ],
      "properties": {
        "code": {
          "$id": "#/properties/error/properties/code",
          "type": "integer",
          "title": "The Code Schema",
          "enum": [
            400
          ]
        },
        "errors": {
          "$id": "#/properties/error/properties/errors",
          "type": "array",
          "title": "The Errors Schema",
          "items": {
            "$id": "#/properties/error/properties/errors/items",
            "type": "object",
            "title": "The Items Schema",
            "required": [
              "domain",
              "message",
              "reason"
            ],
            "properties": {
              "domain": {
                "$id": "#/properties/error/properties/errors/items/properties/domain",
                "type": "string",
                "title": "The Domain Schema",
                "default": "",
                "enum": [
                  "global"
                ],
                "pattern": "^(.*)$"
              },
              "message": {
                "$id": "#/properties/error/properties/errors/items/properties/message",
                "type": "string",
                "title": "The Message Schema",
                "default": "",
                "enum": [
                  "Error parsing ProtoRPC request (Unable to parse request content: Message CombinedContainer is missing required field redirect_uri)"
                ],
                "pattern": "^(.*)$"
              },
              "reason": {
                "$id": "#/properties/error/properties/errors/items/properties/reason",
                "type": "string",
                "title": "The Reason Schema",
                "default": "",
                "enum": [
                  "badRequest"
                ],
                "pattern": "^(.*)$"
              }
            }
          }
        },
        "message": {
          "$id": "#/properties/error/properties/message",
          "type": "string",
          "title": "The Message Schema",
          "default": "",
          "enum": [
            "Error parsing ProtoRPC request (Unable to parse request content: Message CombinedContainer is missing required field redirect_uri)"
          ],
          "pattern": "^(.*)$"
        }
      }
    }
  }
}
json_schema_test_get_auth_url_with_only_redirect_param = json_schema_test_get_auth_url

"""Json Schemas for UnlinkedUserTestCase tests"""
json_schema_test_delete_link_for_unlinked_user = ""  # Delete call returns an empty body
json_schema_test_get_link_status_for_unlinked_user = {
  "definitions": {},
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "http://example.com/root.json",
  "type": "object",
  "title": "The Root Schema",
  "required": [
    "error"
  ],
  "properties": {
    "error": {
      "$id": "#/properties/error",
      "type": "object",
      "title": "The Error Schema",
      "required": [
        "message",
        "code",
        "errors"
      ],
      "properties": {
        "message": {
          "$id": "#/properties/error/properties/message",
          "type": "string",
          "title": "The Message Schema",
          "default": "",
          "enum": [
            "fence link does not exist"
          ],
          "pattern": "^(.*)$"
        },
        "code": {
          "$id": "#/properties/error/properties/code",
          "type": "integer",
          "title": "The Code Schema",
          "default": 0,
          "enum": [
            404
          ]
        },
        "errors": {
          "$id": "#/properties/error/properties/errors",
          "type": "array",
          "title": "The Errors Schema",
          "items": {
            "$id": "#/properties/error/properties/errors/items",
            "type": "object",
            "title": "The Items Schema",
            "required": [
              "reason",
              "domain",
              "message"
            ],
            "properties": {
              "reason": {
                "$id": "#/properties/error/properties/errors/items/properties/reason",
                "type": "string",
                "title": "The Reason Schema",
                "default": "",
                "enum": [
                  "notFound"
                ],
                "pattern": "^(.*)$"
              },
              "domain": {
                "$id": "#/properties/error/properties/errors/items/properties/domain",
                "type": "string",
                "title": "The Domain Schema",
                "default": "",
                "enum": [
                  "global"
                ],
                "pattern": "^(.*)$"
              },
              "message": {
                "$id": "#/properties/error/properties/errors/items/properties/message",
                "type": "string",
                "title": "The Message Schema",
                "default": "",
                "enum": [
                  "fence link does not exist"
                ],
                "pattern": "^(.*)$"
              }
            }
          }
        }
      }
    }
  }
}
json_schema_test_get_link_status_for_invalid_provider = {
  "definitions": {},
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "http://example.com/root.json",
  "type": "object",
  "title": "The Root Schema",
  "required": [
    "error"
  ],
  "properties": {
    "error": {
      "$id": "#/properties/error",
      "type": "object",
      "title": "The Error Schema",
      "required": [
        "message",
        "code",
        "errors"
      ],
      "properties": {
        "message": {
          "$id": "#/properties/error/properties/message",
          "type": "string",
          "title": "The Message Schema",
          "default": "",
          "enum": [
            "provider does_not_exist not found"
          ],
          "pattern": "^(.*)$"
        },
        "code": {
          "$id": "#/properties/error/properties/code",
          "type": "integer",
          "title": "The Code Schema",
          "default": 0,
          "enum": [
            404
          ]
        },
        "errors": {
          "$id": "#/properties/error/properties/errors",
          "type": "array",
          "title": "The Errors Schema",
          "items": {
            "$id": "#/properties/error/properties/errors/items",
            "type": "object",
            "title": "The Items Schema",
            "required": [
              "reason",
              "domain",
              "message"
            ],
            "properties": {
              "reason": {
                "$id": "#/properties/error/properties/errors/items/properties/reason",
                "type": "string",
                "title": "The Reason Schema",
                "default": "",
                "enum": [
                  "notFound"
                ],
                "pattern": "^(.*)$"
              },
              "domain": {
                "$id": "#/properties/error/properties/errors/items/properties/domain",
                "type": "string",
                "title": "The Domain Schema",
                "default": "",
                "enum": [
                  "global"
                ],
                "pattern": "^(.*)$"
              },
              "message": {
                "$id": "#/properties/error/properties/errors/items/properties/message",
                "type": "string",
                "title": "The Message Schema",
                "default": "",
                "enum": [
                  "provider does_not_exist not found"
                ],
                "pattern": "^(.*)$"
              }
            }
          }
        }
      }
    }
  }
}
json_schema_test_get_access_token_for_unlinked_user = {
  "definitions": {},
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "http://example.com/root.json",
  "type": "object",
  "title": "The Root Schema",
  "required": [
    "error"
  ],
  "properties": {
    "error": {
      "$id": "#/properties/error",
      "type": "object",
      "title": "The Error Schema",
      "required": [
        "message",
        "code",
        "errors"
      ],
      "properties": {
        "message": {
          "$id": "#/properties/error/properties/message",
          "type": "string",
          "title": "The Message Schema",
          "default": "",
          "enum": [
            "Could not find refresh token for user"
          ],
          "pattern": "^(.*)$"
        },
        "code": {
          "$id": "#/properties/error/properties/code",
          "type": "integer",
          "title": "The Code Schema",
          "default": 0,
          "enum": [
            400
          ]
        },
        "errors": {
          "$id": "#/properties/error/properties/errors",
          "type": "array",
          "title": "The Errors Schema",
          "items": {
            "$id": "#/properties/error/properties/errors/items",
            "type": "object",
            "title": "The Items Schema",
            "required": [
              "reason",
              "domain",
              "message"
            ],
            "properties": {
              "reason": {
                "$id": "#/properties/error/properties/errors/items/properties/reason",
                "type": "string",
                "title": "The Reason Schema",
                "default": "",
                "enum": [
                  "badRequest"
                ],
                "pattern": "^(.*)$"
              },
              "domain": {
                "$id": "#/properties/error/properties/errors/items/properties/domain",
                "type": "string",
                "title": "The Domain Schema",
                "default": "",
                "enum": [
                  "global"
                ],
                "pattern": "^(.*)$"
              },
              "message": {
                "$id": "#/properties/error/properties/errors/items/properties/message",
                "type": "string",
                "title": "The Message Schema",
                "default": "",
                "enum": [
                  "Could not find refresh token for user"
                ],
                "pattern": "^(.*)$"
              }
            }
          }
        }
      }
    }
  }
}

"""Json Schemas for ExchangeAuthCodeTestCase tests"""
json_schema_test_exchange_auth_code = {
  "definitions": {},
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "http://example.com/root.json",
  "type": "object",
  "title": "The Root Schema",
  "required": [
    "issued_at",
    "username"
  ],
  "properties": {
    "issued_at": {
      "$id": "#/properties/issued_at",
      "type": "string",
      "title": "The Issued_at Schema",
      "default": "",
      "examples": [
        "2020-01-21T15:17:54"
      ],
      "pattern": DATE_REGEX
    },
    "username": {
      "$id": "#/properties/username",
      "type": "string",
      "title": "The Username Schema",
      "default": "",
      "enum": [
        "jimmyb007"
      ],
      "pattern": "^(.*)$"
    }
  }
}

"""Json Schemas for ExchangeAuthCodeNegativeTestCase tests"""
json_schema_test_exchange_auth_code_without_authz_header = {
  "definitions": {},
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "http://example.com/root.json",
  "type": "object",
  "title": "The Root Schema",
  "required": [
    "error"
  ],
  "properties": {
    "error": {
      "$id": "#/properties/error",
      "type": "object",
      "title": "The Error Schema",
      "required": [
        "message",
        "code",
        "errors"
      ],
      "properties": {
        "message": {
          "$id": "#/properties/error/properties/message",
          "type": "string",
          "title": "The Message Schema",
          "default": "",
          "enum": [
            "Request missing Authorization header."
          ],
          "pattern": "^(.*)$"
        },
        "code": {
          "$id": "#/properties/error/properties/code",
          "type": "integer",
          "title": "The Code Schema",
          "default": 0,
          "enum": [
            401
          ]
        },
        "errors": {
          "$id": "#/properties/error/properties/errors",
          "type": "array",
          "title": "The Errors Schema",
          "items": {
            "$id": "#/properties/error/properties/errors/items",
            "type": "object",
            "title": "The Items Schema",
            "required": [
              "reason",
              "domain",
              "message"
            ],
            "properties": {
              "reason": {
                "$id": "#/properties/error/properties/errors/items/properties/reason",
                "type": "string",
                "title": "The Reason Schema",
                "default": "",
                "enum": [
                  "required"
                ],
                "pattern": "^(.*)$"
              },
              "domain": {
                "$id": "#/properties/error/properties/errors/items/properties/domain",
                "type": "string",
                "title": "The Domain Schema",
                "default": "",
                "enum": [
                  "global"
                ],
                "pattern": "^(.*)$"
              },
              "message": {
                "$id": "#/properties/error/properties/errors/items/properties/message",
                "type": "string",
                "title": "The Message Schema",
                "default": "",
                "enum": [
                  "Request missing Authorization header."
                ],
                "pattern": "^(.*)$"
              }
            }
          }
        }
      }
    }
  }
}
json_schema_test_exchange_auth_code_without_redirect_uri_param = {
  "definitions": {},
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "http://example.com/root.json",
  "type": "object",
  "title": "The Root Schema",
  "required": [
    "error"
  ],
  "properties": {
    "error": {
      "$id": "#/properties/error",
      "type": "object",
      "title": "The Error Schema",
      "required": [
        "message",
        "code",
        "errors"
      ],
      "properties": {
        "message": {
          "$id": "#/properties/error/properties/message",
          "type": "string",
          "title": "The Message Schema",
          "default": "",
          "enum": [
            "Error parsing ProtoRPC request (Unable to parse request content: Message CombinedContainer is missing required field redirect_uri)"
          ],
          "pattern": "^(.*)$"
        },
        "code": {
          "$id": "#/properties/error/properties/code",
          "type": "integer",
          "title": "The Code Schema",
          "default": 0,
          "enum": [
            400
          ]
        },
        "errors": {
          "$id": "#/properties/error/properties/errors",
          "type": "array",
          "title": "The Errors Schema",
          "items": {
            "$id": "#/properties/error/properties/errors/items",
            "type": "object",
            "title": "The Items Schema",
            "required": [
              "reason",
              "domain",
              "message"
            ],
            "properties": {
              "reason": {
                "$id": "#/properties/error/properties/errors/items/properties/reason",
                "type": "string",
                "title": "The Reason Schema",
                "default": "",
                "enum": [
                  "badRequest"
                ],
                "pattern": "^(.*)$"
              },
              "domain": {
                "$id": "#/properties/error/properties/errors/items/properties/domain",
                "type": "string",
                "title": "The Domain Schema",
                "default": "",
                "enum": [
                  "global"
                ],
                "pattern": "^(.*)$"
              },
              "message": {
                "$id": "#/properties/error/properties/errors/items/properties/message",
                "type": "string",
                "title": "The Message Schema",
                "default": "",
                "enum": [
                  "Error parsing ProtoRPC request (Unable to parse request content: Message CombinedContainer is missing required field redirect_uri)"
                ],
                "pattern": "^(.*)$"
              }
            }
          }
        }
      }
    }
  }
}
json_schema_test_exchange_auth_code_without_oauthcode_param = {
  "definitions": {},
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "http://example.com/root.json",
  "type": "object",
  "title": "The Root Schema",
  "required": [
    "error"
  ],
  "properties": {
    "error": {
      "$id": "#/properties/error",
      "type": "object",
      "title": "The Error Schema",
      "required": [
        "message",
        "code",
        "errors"
      ],
      "properties": {
        "message": {
          "$id": "#/properties/error/properties/message",
          "type": "string",
          "title": "The Message Schema",
          "default": "",
          "enum": [
            "Error parsing ProtoRPC request (Unable to parse request content: Message CombinedContainer is missing required field oauthcode)"
          ],
          "pattern": "^(.*)$"
        },
        "code": {
          "$id": "#/properties/error/properties/code",
          "type": "integer",
          "title": "The Code Schema",
          "default": 0,
          "enum": [
            400
          ]
        },
        "errors": {
          "$id": "#/properties/error/properties/errors",
          "type": "array",
          "title": "The Errors Schema",
          "items": {
            "$id": "#/properties/error/properties/errors/items",
            "type": "object",
            "title": "The Items Schema",
            "required": [
              "reason",
              "domain",
              "message"
            ],
            "properties": {
              "reason": {
                "$id": "#/properties/error/properties/errors/items/properties/reason",
                "type": "string",
                "title": "The Reason Schema",
                "default": "",
                "enum": [
                  "badRequest"
                ],
                "pattern": "^(.*)$"
              },
              "domain": {
                "$id": "#/properties/error/properties/errors/items/properties/domain",
                "type": "string",
                "title": "The Domain Schema",
                "default": "",
                "enum": [
                  "global"
                ],
                "pattern": "^(.*)$"
              },
              "message": {
                "$id": "#/properties/error/properties/errors/items/properties/message",
                "type": "string",
                "title": "The Message Schema",
                "default": "",
                "enum": [
                  "Error parsing ProtoRPC request (Unable to parse request content: Message CombinedContainer is missing required field oauthcode)"
                ],
                "pattern": "^(.*)$"
              }
            }
          }
        }
      }
    }
  }
}

"""Json Schemas for LinkedUserTestCase tests"""
json_schema_test_get_link_status = json_schema_test_exchange_auth_code
json_schema_test_get_access_token = {
  "definitions": {},
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "http://example.com/root.json",
  "type": "object",
  "title": "The Root Schema",
  "required": [
    "token",
    "expires_at"
  ],
  "properties": {
    "token": {
      "$id": "#/properties/token",
      "type": "string",
      "title": "The Token Schema",
      "default": "",
      "examples": [
        "random.string.accesssToken"
      ],
      "pattern": "^(.*)$"
    },
    "expires_at": {
      "$id": "#/properties/expires_at",
      "type": "string",
      "title": "The Expires_at Schema",
      "default": "",
      "examples": [
        "2020-01-17T22:36:46.479670"
      ],
      "pattern": DATE_REGEX
    }
  }
}
json_schema_test_get_serviceaccount_key = {
  "definitions": {},
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "http://example.com/root.json",
  "type": "object",
  "title": "The Root Schema",
  "required": [
    "data"
  ],
  "properties": {
    "data": {
      "$id": "#/properties/data",
      "type": "object",
      "title": "The Data Schema",
      "required": [
        "private_key",
        "private_key_id",
        "token_uri",
        "auth_provider_x509_cert_url",
        "auth_uri",
        "client_email",
        "client_id",
        "project_id",
        "type",
        "client_x509_cert_url"
      ],
      "properties": {
        "private_key": {
          "$id": "#/properties/data/properties/private_key",
          "type": "string",
          "title": "The Private_key Schema",
          "default": "",
          "examples": [
            "-----BEGIN PRIVATE KEY-----\nMIIEvAIBADANBgkqhki...KnGMvw==\n-----END PRIVATE KEY-----\n"
          ],
          "pattern": "(BEGIN PRIVATE KEY)"
        },
        "private_key_id": {
          "$id": "#/properties/data/properties/private_key_id",
          "type": "string",
          "title": "The Private_key_id Schema",
          "default": "",
          "examples": [
            "9d41d414182a8ff73f944ee89d67c605d1821589"
          ],
          "pattern": "^(.*)$"
        },
        "token_uri": {
          "$id": "#/properties/data/properties/token_uri",
          "type": "string",
          "title": "The Token_uri Schema",
          "default": "",
          "examples": [
            "https://oauth2.googleapis.com/token"
          ],
          "pattern": "^(.*)$"
        },
        "auth_provider_x509_cert_url": {
          "$id": "#/properties/data/properties/auth_provider_x509_cert_url",
          "type": "string",
          "title": "The Auth_provider_x509_cert_url Schema",
          "default": "",
          "examples": [
            "https://www.googleapis.com/oauth2/v1/certs"
          ],
          "pattern": "^(.*)$"
        },
        "auth_uri": {
          "$id": "#/properties/data/properties/auth_uri",
          "type": "string",
          "title": "The Auth_uri Schema",
          "default": "",
          "examples": [
            "https://accounts.google.com/o/oauth2/auth"
          ],
          "pattern": "^(.*)$"
        },
        "client_email": {
          "$id": "#/properties/data/properties/client_email",
          "type": "string",
          "title": "The Client_email Schema",
          "default": "",
          "examples": [
            "mock-provider-user-service-acc@broad-dsde-dev.iam.gserviceaccount.com"
          ],
          "pattern": "^(.*)$"
        },
        "client_id": {
          "$id": "#/properties/data/properties/client_id",
          "type": "string",
          "title": "The Client_id Schema",
          "default": "",
          "examples": [
            "102327840668511205237"
          ],
          "pattern": "^(.*)$"
        },
        "project_id": {
          "$id": "#/properties/data/properties/project_id",
          "type": "string",
          "title": "The Project_id Schema",
          "default": "",
          "examples": [
            "broad-dsde-dev"
          ],
          "pattern": "^(.*)$"
        },
        "type": {
          "$id": "#/properties/data/properties/type",
          "type": "string",
          "title": "The Type Schema",
          "default": "",
          "enum": [
            "service_account"
          ],
          "pattern": "^(.*)$"
        },
        "client_x509_cert_url": {
          "$id": "#/properties/data/properties/client_x509_cert_url",
          "type": "string",
          "title": "The Client_x509_cert_url Schema",
          "default": "",
          "examples": [
            "https://www.googleapis.com/robot/v1/metadata/x509/mock-provider-user-service-acc%40broad-dsde-dev.iam.gserviceaccount.com"
          ],
          "pattern": "^(.*)$"
        }
      }
    }
  }
}

"""Json Schemas for UnlinkLinkedUserTestCase tests"""
json_schema_test_delete_link_for_linked_user = ""  # Delete call returns an empty body
json_schema_test_delete_link_for_invalid_provider = {
  "definitions": {},
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "http://example.com/root.json",
  "type": "object",
  "title": "The Root Schema",
  "required": [
    "error"
  ],
  "properties": {
    "error": {
      "$id": "#/properties/error",
      "type": "object",
      "title": "The Error Schema",
      "required": [
        "message",
        "code",
        "errors"
      ],
      "properties": {
        "message": {
          "$id": "#/properties/error/properties/message",
          "type": "string",
          "title": "The Message Schema",
          "default": "",
          "enum": [
            "provider some-made-up-provider not found"
          ],
          "pattern": "^(.*)$"
        },
        "code": {
          "$id": "#/properties/error/properties/code",
          "type": "integer",
          "title": "The Code Schema",
          "default": 0,
          "enum": [
            404
          ]
        },
        "errors": {
          "$id": "#/properties/error/properties/errors",
          "type": "array",
          "title": "The Errors Schema",
          "items": {
            "$id": "#/properties/error/properties/errors/items",
            "type": "object",
            "title": "The Items Schema",
            "required": [
              "reason",
              "domain",
              "message"
            ],
            "properties": {
              "reason": {
                "$id": "#/properties/error/properties/errors/items/properties/reason",
                "type": "string",
                "title": "The Reason Schema",
                "default": "",
                "enum": [
                  "notFound"
                ],
                "pattern": "^(.*)$"
              },
              "domain": {
                "$id": "#/properties/error/properties/errors/items/properties/domain",
                "type": "string",
                "title": "The Domain Schema",
                "default": "",
                "enum": [
                  "global"
                ],
                "pattern": "^(.*)$"
              },
              "message": {
                "$id": "#/properties/error/properties/errors/items/properties/message",
                "type": "string",
                "title": "The Message Schema",
                "default": "",
                "enum": [
                  "provider some-made-up-provider not found"
                ],
                "pattern": "^(.*)$"
              }
            }
          }
        }
      }
    }
  }
}

"""Json Schemas for UserCredentialsTestCase tests"""
json_schema_test_token = ""  # Creates a token but no API call is made
json_schema_test_user_info_for_delegated_user = {
  "definitions": {},
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "http://example.com/root.json",
  "type": "object",
  "title": "The Root Schema",
  "required": [
    "family_name",
    "name",
    "picture",
    "locale",
    "email",
    "given_name",
    "id",
    "hd",
    "verified_email"
  ],
  "properties": {
    "family_name": {
      "$id": "#/properties/family_name",
      "type": "string",
      "title": "The Family_name Schema",
      "default": "",
      "enum": [
        "Granger"
      ],
      "pattern": "^(.*)$"
    },
    "name": {
      "$id": "#/properties/name",
      "type": "string",
      "title": "The Name Schema",
      "default": "",
      "enum": [
        "Hermione Granger"
      ],
      "pattern": "^(.*)$"
    },
    "picture": {
      "$id": "#/properties/picture",
      "type": "string",
      "title": "The Picture Schema",
      "default": "",
      "enum": [
        "https://lh3.googleusercontent.com/-vd-xJM0bRSk/AAAAAAAAAAI/AAAAAAAAAAA/ACHi3rc7YyU2qNlHlydOOxp68LcWSB22tw/photo.jpg"
      ],
      "pattern": "^(.*)$"
    },
    "locale": {
      "$id": "#/properties/locale",
      "type": "string",
      "title": "The Locale Schema",
      "default": "",
      "enum": [
        "en"
      ],
      "pattern": "^(.*)$"
    },
    "email": {
      "$id": "#/properties/email",
      "type": "string",
      "title": "The Email Schema",
      "default": "",
      "enum": [
        "hermione.owner@test.firecloud.org"
      ],
      "pattern": "^(.*)$"
    },
    "given_name": {
      "$id": "#/properties/given_name",
      "type": "string",
      "title": "The Given_name Schema",
      "default": "",
      "enum": [
        "Hermione"
      ],
      "pattern": "^(.*)$"
    },
    "id": {
      "$id": "#/properties/id",
      "type": "string",
      "title": "The Id Schema",
      "default": "",
      "enum": [
        "110530393451290928813"
      ],
      "pattern": "^(.*)$"
    },
    "hd": {
      "$id": "#/properties/hd",
      "type": "string",
      "title": "The Hd Schema",
      "default": "",
      "enum": [
        "test.firecloud.org"
      ],
      "pattern": "^(.*)$"
    },
    "verified_email": {
      "$id": "#/properties/verified_email",
      "type": "boolean",
      "title": "The Verified_email Schema",
      "enum": [
        True
      ],
      "pattern": "^(.*)$"
    }
  }
}
