import os
import typing as t
from .interfaces import ISecrets


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
