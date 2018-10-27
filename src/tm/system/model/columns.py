# Standard Library

import datetime

# SQLAlchemy
from sqlalchemy import DateTime


class UTCDateTime(DateTime):
    """An SQLAlchemy DateTime column that explicitly uses timezone aware dates and only accepts UTC."""

    def __init__(self, *args, **kwargs):
        # If there is an explicit timezone we accept UTC only
        if "timezone" in kwargs:
            if kwargs["timezone"] not in (datetime.timezone.utc, True):
                raise ValueError(
                    "Only 'datetime.timezone.utc' or True accepted"
                    " as timezone for '{}'".format(self.__class__.__name__)
                )

        kwargs = kwargs.copy()
        # Using an explict 'True' ensures no false positives
        # on alembic migrations due to failed equality test.
        # (issue #162)
        kwargs["timezone"] = True
        super(UTCDateTime, self).__init__(**kwargs)

    def _dialect_info(self, dialect):
        return super(UTCDateTime, self)._dialect_info(dialect)


# Don't expose sqlalchemy_utils internals as they may go away
__all__ = ["UTCDateTime"]
