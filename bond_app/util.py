import os


def get_provider_secrets(config, provider: str):
    if os.environ.get("BOND_ENV_SECRETS"):
        provider_normalized = provider.upper().replace("-", "_")
        client_id = os.environ.get(f"{provider_normalized}_CLIENT_ID")
        client_secret = os.environ.get(f"{provider_normalized}_CLIENT_SECRET")
    else:
        client_id = config.get(provider, 'CLIENT_ID')
        client_secret = config.get(provider, 'CLIENT_SECRET')
    return client_id, client_secret
