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
    config.include('.conf')
    config.include('.conf.secrets')
    config.include('.conf.templates')
    config.include('.conf.models')
    config.include('.routes')
    config.scan()
    app = config.make_wsgi_app()
    # Sanity Check
    check = asbool(config.registry.settings.get("tm.sanity_check", True))
    config.db_sanity_check(check)
    config.commit()

    return app



def make_wsgi_app(self, sanity_check=True):
    """Create WSGI application from the current setup.

    :param sanity_check: True if perform post-initialization sanity checks.
    :return: WSGI application
    """
    app = self.config.make_wsgi_app()
    # Carry the initializer around so we can access it in tests

    app.initializer = self

    if "sanity_check" in self.global_config:
        # Command line scripts can override this when calling bootstrap()
        sanity_check = asbool(self.global_config["sanity_check"])
    else:
        sanity_check = asbool(self.settings.get("lesspaper.base.sanity_check", True))

    if sanity_check:
        self.sanity_check()

    app = self.wrap_wsgi_app(app)

    return app

