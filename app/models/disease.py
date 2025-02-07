from uuid import uuid4

from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import UUID

from db.base_class import Base


class Disease(Base):
    __tablename__ = "disease"
    id = Column(UUID(as_uuid=True), primary_key=True, unique=True, nullable=False, default=uuid4)

    name = Column(String, nullable=False)
    eppo_code = Column(String, nullable=False)
    description = Column(String, nullable=True)

    gdd_points = Column(String, nullable=False)