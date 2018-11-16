def config_declarative_models():
    from tm.system.model.meta import Base
    from tm.system.user import models


    attach_model_to_base(models.User, Base)
    attach_model_to_base(models.Group, Base)
    attach_model_to_base(models.Activation, Base)
    attach_model_to_base(models.UserGroup, Base)


def attach_model_to_base(ModelClass: type, Base: type):
    """Dynamically add a model to chosen SQLAlchemy Base class.

    More flexibility is gained by not inheriting from SQLAlchemy declarative base and instead plugging in models during the configuration time more.

    Directly inheriting from SQLAlchemy Base class has non-undoable side effects. All models automatically pollute SQLAlchemy namespace and may e.g. cause problems with conflicting table names. This also allows @declared_attr to access Pyramid registry.
    """
    from sqlalchemy.ext.declarative import instrument_declarative
    instrument_declarative(ModelClass, registry=Base._decl_class_registry, metadata=Base.metadata)
