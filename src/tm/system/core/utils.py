import os
import typing as t
from .interfaces import ISecrets


from tm.system.http import Request


def get_config_url(request: Request, config_key: str) -> str:
    """Route to a given URL from settings file."""
    settings = request.registry.settings

    try:
        return settings[config_key]
    except KeyError:
        return settings[config_key]


def get_config_route(request: Request, config_key: str) -> str:
    """Route to a given URL from settings file."""
    return request.route_url(get_config_url(request, config_key))


def get_secrets(registry) -> dict:
    """Get the secrets provider dictionary.

    :return: A dictionary containing secrets having {ini sectionid}.{key} as keys.
    """
    return registry.getUtility(ISecrets)


def replace_env_vars(settings: dict) -> dict:
    """Expand all environment variables in a settings dictionary.

    ref: http://stackoverflow.com/a/16446566
    :returns: Dictionary with settings
    """
    return {key: _expandvars(value) for key, value in settings.items()}


def _expandvars(value: t.Any) -> t.Any:
    processed = value
    if isinstance(value, dict):
        processed = replace_env_vars(value)
    elif isinstance(value, (str, bytes)):
        processed = os.path.expandvars(value)
    return processed
