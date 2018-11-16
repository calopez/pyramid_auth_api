"""Default template variables."""
# Standard Library
import datetime
import logging

# Pyramid
from pyramid.events import BeforeRender

# System
from tm.utils.time import now


logger = logging.getLogger(__name__)


_template_variables = {}


def var(name):
    """Decorator to mark template variables for documentation."""

    def _inner(func):
        _template_variables[name] = func
        return func

    return _inner


@var("site_home_url")
def site_name(request, registry, settings):
    """Expose website name from ``tm.site_name`` config variable to templates.

    Example:

    .. code-block:: html+jinja

        <h2><a href="{{ site_home_url }}">{{ site_name }}</a></h2>

    """
    return settings["tm.site_home_url"]

@var("site_name")
def site_name(request, registry, settings):
    """Expose website name from ``tm.site_name`` config variable to templates.

    Example:

    .. code-block:: html+jinja

        <div class="jumbotron text-center">
            <h1>{{ site_name }}</h1>
            <p class="lead text-center">
                {{ site_tag_line }}
            </p>
        </div>

    """
    return settings["tm.site_name"]


@var("site_title")
def site_title(request, registry, settings):
    """Expose website name from ``tm.site_title`` config variable to templates.

    This is the default ``<title>`` tag.

    Example:

    .. code-block:: html+jinja

        <meta>
            <title>My page - {{ site_title }}</title>
        </meta>

    """
    # Use .get() for BBB
    return settings.get("tm.site_title", "")


@var("site_url")
def site_url(request, registry, settings):
    """Expose website URL from ``tm.site_url`` config variable to templates.

    .. note ::

        You should not use this variable in web page templates. This variable is intended for cases where one needs templating without running a web server.

    The correct way to get the home URL of your website is:

    .. code-block:: html+jinja

        <a href="{{ request.route_url('home') }}">Home</a>

    """
    return settings["tm.site_url"]


@var("site_author")
def site_author(request, registry, settings):
    """Expose website URL from ``tm.site_author`` config variable to templates.

    This is used in footer to display the site owner.
    """
    return settings["tm.site_author"]


@var("site_tag_line")
def site_tag_line(request, registry, settings):
    """Expose website URL from ``tm.site_tag_line`` config variable to templates.

    This is used on the default front page to catch the attention of audience.
    """
    return settings["tm.site_tag_line"]


@var("site_email_prefix")
def site_email_prefix(request, registry, settings):
    """Expose website URL from ``tm.site_email_prefix`` config variable to templates.

    This is used as the subject prefix in outgoing email. E.g. if the value is ``SuperSite`` you'll email subjects::

        [SuperSite] Welcome to www.supersite.com

    """
    return settings["tm.site_email_prefix"]


@var("site_time_zone")
def site_time_zone(request, registry, settings):
    """Expose website URL from ``tm.site_time_zone`` config variable to templates.

    By best practices, all dates and times should be stored in the database using :term:`UTC` time. This setting
    allows quickly convert dates and times to your local time.

    Example:

    .. code-block:: html+jinja

        <p>
            <strong>Bar opens</strong>:
            {{ opening_at|friendly_time(timezone=site_time_zone) }}
        </p>

    Default value is ``UTC``.

    See `timezone abbreviation list <https://en.wikipedia.org/wiki/List_of_time_zone_abbreviations>`_.
    """
    return settings.get("tm.site_timezone", "UTC")


@var("now")
def _now(request, registry, settings):
    """Get the current time as :term:`UTC`.

    :py:func:`tm.system.utils.time.now` function.

    Example:

    .. code-block: html+jinja

      <footer class="footer">
        <div class="container-fluid">
          <p class="copyright pull-right">
            &copy; {{ now().year }} {{ site_author }}
          </p>
        </div>
      </footer>

    """
    return now


@var("timedelta")
def _timedelta(request, registry, settings):
    """Expose Python timedelta class to templates, so you can do relative time calculations.

    For more information see :py:class:`datetime.timedelta`.

    Example:

    .. code-block: html+jinja

        <div class="panel panel-default panel-admin">
          <div class="panel-body">
            <h2>
                Current power generation
                (as generated {{ (now() - timedelta(days=14))|arrow_format("YYYY-MM-DD")}}*)
            </h2>

            <div id="super-nice-graph"></div>

            <p>* Incoming data delayed two weeks</p>

          </div>
        </div>

    """
    return datetime.timedelta


def includeme(config):

    def on_before_render(event):
        # Augment Pyramid template renderers with these extra variables and deal with JS placement

        request = event["request"]

        for name, func in _template_variables.items():
            event[name] = func(request, request.registry, request.registry.settings)

    config.add_subscriber(on_before_render, BeforeRender)
