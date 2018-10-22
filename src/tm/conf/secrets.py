from pyramid.settings import asbool

def includeme(config):
    """Read secrets configuration file.

    Stores API keys, such.
    """
    # Secret configuration directives
    from tm.system.utils.secrets import read_ini_secrets
    from tm.system.core.interfaces import ISecrets

    # settings = self.settings

    secrets_file = config.registry.settings.get("tm.secrets_file")
    if not secrets_file:
        return {}

    strict = asbool(config.registry.settings.get("tm.secrets_strict", True))

    _secrets = read_ini_secrets(secrets_file, strict=strict)
    config.registry.registerUtility(_secrets, ISecrets)
    secret_settings = {k.replace('app:main.', ''): v for k, v in _secrets.items() if k.startswith('app:main.')}
    # settings.update(secret_settings)
    config.registry.settings.update(secret_settings)

