"""Route related helpers."""

# Pyramid
from pyramid.interfaces import IRequest


def get_config_route(request: IRequest, config_key: str) -> str:
    """Route to a given URL from settings file."""
    settings = request.registry.settings

    try:
        return request.route_url(settings[config_key])
    except KeyError:
        return settings[config_key]
