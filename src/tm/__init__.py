# -*- coding: utf-8 -*-
import os
import typing as t

from pkg_resources import get_distribution, DistributionNotFound

try:
    # Change here if project is renamed and does not equal the package name
    dist_name = __name__
    __version__ = get_distribution(dist_name).version
except DistributionNotFound:
    __version__ = 'unknown'
finally:
    del get_distribution, DistributionNotFound


from pyramid.config import Configurator


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """

    config = Configurator(settings=expandvars_dict(settings))
    config.include('.conf.secrets')

    config.include('pyramid_jinja2')
    config.include('.models')
    config.include('.routes')
    config.scan()
    return config.make_wsgi_app()


def expandvars_dict(settings: dict) -> dict:
    """Expand all environment variables in a settings dictionary.

    ref: http://stackoverflow.com/a/16446566
    :returns: Dictionary with settings
    """
    return {key: _expandvars(value) for key, value in settings.items()}


def _expandvars(value: t.Any) -> t.Any:
    processed = value
    if isinstance(value, dict):
        processed = expandvars_dict(value)
    elif isinstance(value, (str, bytes)):
        processed = os.path.expandvars(value)
    return processed


