def includeme(config):
    from tm.system.model import config_declarative_models
    config_declarative_models()

    config.include('tm.system.model.meta')



