def includeme(config):
    config.include('.templates')
    config.include('.routes')
    config.include('.models')
    config.include('.auth')
    config.include('.federated_login')
    config.include('.sanity_check')
