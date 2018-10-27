from sqlalchemy import (
    Column,
    Index,
    Integer,
    String,
)
from sqlalchemy_utils.types.uuid import UUIDType

from uuid import uuid4
from tm.system.model.meta import Base
from tm.system.utils.time import now
from tm.system.model.columns import UTCDateTime



class MyModel(Base):
    __tablename__ = 'models'
    id = Column(Integer, primary_key=True)
    value = Column(Integer)
    uuid = Column(UUIDType, default=uuid4)
    name = Column(String(256), nullable=True, unique=True)
    created_at = Column(UTCDateTime, default=now)
    updated_at = Column(UTCDateTime, onupdate=now)


Index('my_index', MyModel.name, unique=True, mysql_length=255)
