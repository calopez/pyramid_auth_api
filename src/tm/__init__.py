# -*- coding: utf-8 -*-
import os
import typing as t

from pkg_resources import get_distribution, DistributionNotFound
from pyramid.settings import asbool

try:
    # Change here if project is renamed and does not equal the package name
    dist_name = __name__
    __version__ = get_distribution(dist_name).version
except DistributionNotFound:
    __version__ = 'unknown'
finally:
    del get_distribution, DistributionNotFound


from pyramid.config import Configurator
from tm.system.core.utils import replace_env_vars


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """

    config = Configurator(settings=replace_env_vars(settings))
    # Third Party
    config.include('cornice')

    # Initializer
    config.add_static_view('static', 'tm:static', cache_max_age=3600)
    config.include('.config.secrets')
    config.include('.config.system')
    config.include('.config.app')

    # Scan for configuration
    config.scan()

    # Initialize WSGI/Server Application
    app = config.make_wsgi_app()

    # Sanity Check
    config.db_sanity_check()
    return app
