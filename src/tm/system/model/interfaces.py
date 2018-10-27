# Pyramid
from zope.interface import Interface


class IModel(Interface):
    """Marker the class which declares SQLAlchemy model.

    We cannot implicitly assume everything is inherited from ``.meta.Base`` because there could be plugin models and such.
    """


class ISQLAlchemySessionFactory(Interface):
    """Provides way to hook in a custom SQLALchemy session creator.

    Use cases include pooling, setting up different session logic for tests, etc.
    """
