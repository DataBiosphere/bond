"""
Json Schemas for api_test.py

Generate, modify, or validate a schema from json here: https://jsonschema.net/

Use "enum" to ensure exact values. Remove superfluous fields.
 """

DATE_REGEX = "20..-..-..T..:..:.."  # valid through 2099

"""Json Schemas for PublicApiTestCase tests"""
json_schema_test_status = {
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": [
    "ok",
    "subsystems"
  ],
  "properties": {
    "ok": {
      "type": "boolean",
      "enum": [True]
    },
    "subsystems": {
      "type": "array",
      "items": {
        "minItems": 5,
        "type": "object",
        "required": [
          "message",
          "ok",
          "subsystem"
        ],
        "properties": {
          "message": {
            "type": "string",
          },
          "ok": {
            "type": "boolean",
            "enum": [True]
          },
          "subsystem": {
            "type": "string",
            "enum": [
              "fence",
              "dcf-fence",
              "anvil",
              "kids-first",
              "cache",
              "datastore",
              "sam"
            ],
          }
        }
      }
    }
  }
}
json_schema_test_list_providers = {
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": [
    "providers"
  ],
    "properties": {
        "providers": {
            "type": "array",
            "items": {
                "type": "string",
                "minItems": 2,
                "enum": ["fence", "dcf-fence", "anvil", "kids-first"]
            }
        }
    },
}
json_schema_test_get_auth_url = {
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": [
    "url"
  ],
  "properties": {
    "url": {
      "type": "string",
      "examples": [
        "https://staging.datastage.io/user/oauth2/authorize?response_type=code&client_id=4EmZnWKVMoPyhdJMh7EB8SSl3Uojo20QfsAR77gu&redirect_uri=http%3A%2F%2Flocal.broadinstitute.org%2F%23fence-callback&scope=openid+google_credentials&state=eyJmb28iPSJiYXIifQ%3D%3D&idp=fence"
      ],
      "pattern": "(https)(.*)(response_type)(.*)(client_id)(.*)(redirect_uri)(.*)(state)(.*)"
    }
  }
}
json_schema_test_get_auth_url_without_params = {
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": [
    "error"
  ],
  "properties": {
    "error": {
      "type": "object",
      "required": [
        "code",
        "errors",
        "message"
      ],
      "properties": {
        "code": {
          "type": "integer",
          "enum": [
            400
          ]
        },
        "errors": {
          "type": "array",
          "items": {
            "type": "object",
            "required": [
              "domain",
              "message",
              "reason"
            ],
            "properties": {
              "domain": {
                "type": "string",
                "enum": [
                  "global"
                ],
              },
              "message": {
                "type": "string",
                "enum": [
                  "The browser (or proxy) sent a request that this server could not understand."
                ],
              },
              "reason": {
                "type": "string",
                "enum": [
                  "badRequest"
                ],
              }
            }
          }
        },
        "message": {
          "type": "string",
          "enum": [
            "The browser (or proxy) sent a request that this server could not understand."
          ],
        }
      }
    }
  }
}
json_schema_test_get_auth_url_with_only_redirect_param = json_schema_test_get_auth_url

"""Json Schemas for UnlinkedUserTestCase tests"""
json_schema_test_delete_link_for_unlinked_user = ""  # Delete call returns an empty body
json_schema_test_get_link_status_for_unlinked_user = {
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": [
    "error"
  ],
  "properties": {
    "error": {
      "type": "object",
      "required": [
        "message",
        "code",
        "errors"
      ],
      "properties": {
        "message": {
          "type": "string",
          "enum": [
            "fence link does not exist. Consider re-linking your account."
          ],
        },
        "code": {
          "type": "integer",
          "default": 0,
          "enum": [
            404
          ]
        },
        "errors": {
          "type": "array",
          "items": {
            "type": "object",
            "required": [
              "reason",
              "domain",
              "message"
            ],
            "properties": {
              "reason": {
                "type": "string",
                "enum": [
                  "notFound"
                ],
              },
              "domain": {
                "type": "string",
                "enum": [
                  "global"
                ],
              },
              "message": {
                "type": "string",
                "enum": [
                  "fence link does not exist. Consider re-linking your account."
                ],
              }
            }
          }
        }
      }
    }
  }
}
json_schema_test_get_link_status_for_invalid_provider = {
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": [
    "error"
  ],
  "properties": {
    "error": {
      "type": "object",
      "required": [
        "message",
        "code",
        "errors"
      ],
      "properties": {
        "message": {
          "type": "string",
          "enum": [
            "provider does_not_exist not found"
          ],
        },
        "code": {
          "type": "integer",
          "default": 0,
          "enum": [
            404
          ]
        },
        "errors": {
          "type": "array",
          "items": {
            "type": "object",
            "required": [
              "reason",
              "domain",
              "message"
            ],
            "properties": {
              "reason": {
                "type": "string",
                "enum": [
                  "notFound"
                ],
              },
              "domain": {
                "type": "string",
                "enum": [
                  "global"
                ],
              },
              "message": {
                "type": "string",
                "enum": [
                  "provider does_not_exist not found"
                ],
              }
            }
          }
        }
      }
    }
  }
}
json_schema_test_get_access_token_for_unlinked_user = {
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": [
    "error"
  ],
  "properties": {
    "error": {
      "type": "object",
      "required": [
        "message",
        "code",
        "errors"
      ],
      "properties": {
        "message": {
          "type": "string",
          "examples": [
            "Could not find refresh token for sam_user_id: 110530393451290928813 provider_name: fence\nConsider relinking your account to Bond."
          ],
          "pattern":
            "Could not find refresh token for sam_user_id: (.*) provider_name: (.*)\nConsider relinking your account to Bond."
        },
        "code": {
          "type": "integer",
          "default": 0,
          "enum": [
            404
          ]
        },
        "errors": {
          "type": "array",
          "items": {
            "type": "object",
            "required": [
              "reason",
              "domain",
              "message"
            ],
            "properties": {
              "reason": {
                "type": "string",
                "enum": [
                  "notFound"
                ],
              },
              "domain": {
                "type": "string",
                "enum": [
                  "global"
                ],
              },
              "message": {
                "type": "string",
                "examples": [
                  "Could not find refresh token for sam_user_id: 110530393451290928813 provider_name: fence\nConsider relinking your account to Bond."
                ],
                "pattern":
                  "Could not find refresh token for sam_user_id: (.*) provider_name: (.*)\nConsider relinking your account to Bond."
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
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": [
    "issued_at",
    "username"
  ],
  "properties": {
    "issued_at": {
      "type": "string",
      "examples": [
        "2020-01-21T15:17:54"
      ],
      "pattern": DATE_REGEX
    },
    "username": {
      "type": "string",
      "enum": [
        "jimmyb007"
      ],
    }
  }
}

"""Json Schemas for ExchangeAuthCodeNegativeTestCase tests"""
json_schema_test_exchange_auth_code_without_authz_header = {
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": [
    "error"
  ],
  "properties": {
    "error": {
      "type": "object",
      "required": [
        "message",
        "code",
        "errors"
      ],
      "properties": {
        "message": {
          "type": "string",
          "enum": [
            "Request missing Authorization header."
          ],
        },
        "code": {
          "type": "integer",
          "default": 0,
          "enum": [
            401
          ]
        },
        "errors": {
          "type": "array",
          "items": {
            "type": "object",
            "required": [
              "reason",
              "domain",
              "message"
            ],
            "properties": {
              "reason": {
                "type": "string",
                "enum": [
                  "required"
                ],
              },
              "domain": {
                "type": "string",
                "enum": [
                  "global"
                ],
              },
              "message": {
                "type": "string",
                "enum": [
                  "Request missing Authorization header."
                ],
              }
            }
          }
        }
      }
    }
  }
}
json_schema_test_exchange_auth_code_without_redirect_uri_param = {
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": [
    "error"
  ],
  "properties": {
    "error": {
      "type": "object",
      "required": [
        "message",
        "code",
        "errors"
      ],
      "properties": {
        "message": {
          "type": "string",
          "enum": [
            "The browser (or proxy) sent a request that this server could not understand."
          ],
        },
        "code": {
          "type": "integer",
          "default": 0,
          "enum": [
            400
          ]
        },
        "errors": {
          "type": "array",
          "items": {
            "type": "object",
            "required": [
              "reason",
              "domain",
              "message"
            ],
            "properties": {
              "reason": {
                "type": "string",
                "enum": [
                  "badRequest"
                ],
              },
              "domain": {
                "type": "string",
                "enum": [
                  "global"
                ],
              },
              "message": {
                "type": "string",
                "enum": [
                  "The browser (or proxy) sent a request that this server could not understand."
                ],
              }
            }
          }
        }
      }
    }
  }
}
json_schema_test_exchange_auth_code_without_oauthcode_param = {
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": [
    "error"
  ],
  "properties": {
    "error": {
      "type": "object",
      "required": [
        "message",
        "code",
        "errors"
      ],
      "properties": {
        "message": {
          "type": "string",
          "enum": [
            "The browser (or proxy) sent a request that this server could not understand."
          ],
        },
        "code": {
          "type": "integer",
          "default": 0,
          "enum": [
            400
          ]
        },
        "errors": {
          "type": "array",
          "items": {
            "type": "object",
            "required": [
              "reason",
              "domain",
              "message"
            ],
            "properties": {
              "reason": {
                "type": "string",
                "enum": [
                  "badRequest"
                ],
              },
              "domain": {
                "type": "string",
                "enum": [
                  "global"
                ],
              },
              "message": {
                "type": "string",
                "enum": [
                  "The browser (or proxy) sent a request that this server could not understand."
                ],
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
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": [
    "token",
    "expires_at"
  ],
  "properties": {
    "token": {
      "type": "string",
      "examples": [
        "random.string.accesssToken"
      ],
    },
    "expires_at": {
      "type": "string",
      "examples": [
        "2020-01-17T22:36:46.479670"
      ],
      "pattern": DATE_REGEX
    }
  }
}
json_schema_test_get_serviceaccount_key = {
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": [
    "data"
  ],
  "properties": {
    "data": {
      "type": "object",
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
          "type": "string",
          "examples": [
            "-----BEGIN PRIVATE KEY-----\nMIIEvAIBADANBgkqhki...KnGMvw==\n-----END PRIVATE KEY-----\n"
          ],
          "pattern": "(BEGIN PRIVATE KEY)"
        },
        "private_key_id": {
          "type": "string",
          "examples": [
            "9d41d414182a8ff73f944ee89d67c605d1821589"
          ],
        },
        "token_uri": {
          "type": "string",
          "examples": [
            "https://oauth2.googleapis.com/token"
          ],
        },
        "auth_provider_x509_cert_url": {
          "type": "string",
          "examples": [
            "https://www.googleapis.com/oauth2/v1/certs"
          ],
        },
        "auth_uri": {
          "type": "string",
          "examples": [
            "https://accounts.google.com/o/oauth2/auth"
          ],
        },
        "client_email": {
          "type": "string",
          "examples": [
            "mock-provider-user-service-acc@broad-dsde-dev.iam.gserviceaccount.com"
          ],
        },
        "client_id": {
          "type": "string",
          "examples": [
            "102327840668511205237"
          ],
        },
        "project_id": {
          "type": "string",
          "examples": [
            "broad-dsde-dev"
          ],
        },
        "type": {
          "type": "string",
          "enum": [
            "service_account"
          ],
        },
        "client_x509_cert_url": {
          "type": "string",
          "examples": [
            "https://www.googleapis.com/robot/v1/metadata/x509/mock-provider-user-service-acc%40broad-dsde-dev.iam.gserviceaccount.com"
          ],
        }
      }
    }
  }
}
json_schema_test_get_serviceaccount_accesstoken = {
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": [
    "token"
  ],
  "properties": {
    "token": {
      "type": "string",
      "pattern": "ya29"
    }
  }
}

"""Json Schemas for UnlinkLinkedUserTestCase tests"""
json_schema_test_delete_link_for_linked_user = ""  # Delete call returns an empty body
json_schema_test_delete_link_for_invalid_provider = {
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": [
    "error"
  ],
  "properties": {
    "error": {
      "type": "object",
      "required": [
        "message",
        "code",
        "errors"
      ],
      "properties": {
        "message": {
          "type": "string",
          "enum": [
            "provider some-made-up-provider not found"
          ],
        },
        "code": {
          "type": "integer",
          "default": 0,
          "enum": [
            404
          ]
        },
        "errors": {
          "type": "array",
          "items": {
            "type": "object",
            "required": [
              "reason",
              "domain",
              "message"
            ],
            "properties": {
              "reason": {
                "type": "string",
                "enum": [
                  "notFound"
                ],
              },
              "domain": {
                "type": "string",
                "enum": [
                  "global"
                ],
              },
              "message": {
                "type": "string",
                "enum": [
                  "provider some-made-up-provider not found"
                ],
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
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
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
      "type": "string",
      "enum": [
        "Granger"
      ],
    },
    "name": {
      "type": "string",
      "enum": [
        "Hermione Granger"
      ],
    },
    "picture": {
      "type": "string",
      "example": [
        "https://lh3.googleusercontent.com/-vd-xJM0bRSk/AAAAAAAAAAI/AAAAAAAAAAA/ACHi3rc7YyU2qNlHlydOOxp68LcWSB22tw/photo.jpg"
      ],
    },
    "locale": {
      "type": "string",
      "enum": [
        "en"
      ],
    },
    "email": {
      "type": "string",
      "enum": [
        "hermione.owner@test.firecloud.org",
        "hermione.owner@quality.firecloud.org"
      ]
    },
    "given_name": {
      "type": "string",
      "enum": [
        "Hermione"
      ],
    },
    "id": {
      "type": "string",
      "example": [
        "110530393451290928813"
      ],
    },
    "hd": {
      "type": "string",
      "enum": [
        "test.firecloud.org",
        "quality.firecloud.org"
      ],
    },
    "verified_email": {
      "type": "boolean",
      "enum": [
        True
      ],
    }
  }
}
