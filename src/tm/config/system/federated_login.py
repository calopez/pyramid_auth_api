import logging
from pyramid.path import DottedNameResolver
from pyramid.settings import aslist

from tm.system.core.interfaces import ISecrets
from pyramid.interfaces import IRequest


def includeme(config):
    """Configure federated authentication (OAuth).

    Set up Authomatic login services.

    Read enabled federated authentication methods from the configuration file.
    """
    # TODO: Refactor this to separate functions, not implementation is not very clean

    import authomatic
    from tm.system.user.interfaces import IAuthomatic, ISocialLoginMapper , IOAuthLoginService
    from tm.system.user.oauthloginservice import DefaultOAuthLoginService

    secrets = config.registry.queryUtility(ISecrets)

    config.add_route('login_social', '/oauth/login/{provider_name}')
    config.add_route('access_token', '/oauth/accesstoken')

    social_logins = aslist(config.registry.settings.get("tm.social_logins", ""))

    if not social_logins:
        return

    authomatic_secret = secrets["authomatic.secret"]

    resolver = DottedNameResolver()

    # Quick helper to access settings
    def xget(section, key):
        value = secrets.get(section + "." + key)
        assert value is not None, "Missing secret settings for [{}]: {}".format(section, key)
        return value

    authomatic_config = {}
    for login in social_logins:

        authomatic_config[login] = {}
        authomatic_config[login]["consumer_key"] = xget(login, "consumer_key")
        authomatic_config[login]["consumer_secret"] = xget(login, "consumer_secret")
        authomatic_config[login]["scope"] = aslist(xget(login, "scope"))

        # TODO: Class is not a real secret, think smarter way to do this
        authomatic_config[login]["class_"] = resolver.resolve(xget(login, "class"))

        # Construct social login mapper
        mapper_class = xget(login, "mapper")
        if mapper_class:
            mapper_class = resolver.resolve(mapper_class)
            mapper = mapper_class(config.registry, login)
            config.registry.registerUtility(mapper, ISocialLoginMapper, name=login)

    # Store instance

    # Pass explicitly a logger so that we can control the log level
    logger = logging.getLogger("authomatic")

    instance = authomatic.Authomatic(config=authomatic_config, secret=authomatic_secret, logger=logger)
    config.registry.registerUtility(instance, IAuthomatic)

    config.registry.registerAdapter(factory=DefaultOAuthLoginService, required=(IRequest,),
                                         provided=IOAuthLoginService)