from pyramid.events import NewRequest
from pyramid.response import Response

__cors_headers = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'POST,GET,DELETE,PUT,OPTIONS',
    'Access-Control-Allow-Headers': 'Origin, Content-Type, Accept, Authorization',
    'Access-Control-Expose-Headers': 'Authorization',
    'Access-Control-Allow-Credentials': 'true',
    'Access-Control-Max-Age': '1728000',
}

def cors_preflight_tween_factory(handler, registry):
    # one-time configuration code goes here

    def cors_tween(request):
        if request.method == 'OPTIONS':
            response = Response(json={})
        else:
            # before
            response = handler(request) # <-- be-TWEEN
            # after

        response.headers.update(__cors_headers)
        return response

    return cors_tween

def includeme(config):
    config.add_tween('tm.config.cors.cors_preflight_tween_factory')


