from pyramid.security import Allow, Authenticated , Everyone


class Root:

    def __acl__(self):
        return [
            (Allow, Authenticated, ('authenticated',)),
        ]

    def __init__(self, request):
        pass


def includeme(config):
    """Set up authentication and authorization policies.

    For more information see Pyramid auth documentation.
    """
    from tm.system.auth.principals import resolve_principals
    from tm.system.auth.authentication import get_request_user
    from pyramid.authorization import ACLAuthorizationPolicy

    # Enable JWT authentication.
    config.include('pyramid_jwt')
    config.set_root_factory(Root)
    authz_policy = ACLAuthorizationPolicy()
    config.set_authorization_policy(authz_policy)
    config.set_jwt_authentication_policy('secret',
                                         auth_type='Bearer',
                                         callback=resolve_principals,
                                         audience="localhost"
                                         )

    # Grab incoming auth details changed events
    from tm.system.auth import subscribers
    config.scan(subscribers)

    # Experimental support for transaction aware properties
    try:
        from pyramid_tm.reify import transaction_aware_reify
        config.add_request_method(
            callable=transaction_aware_reify(config, get_request_user),
            name="user",
            property=True,
            reify=False)
    except ImportError:
        config.add_request_method(get_request_user, 'user', reify=True)
