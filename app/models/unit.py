from sqlalchemy import Column, Integer, String

from db.base_class import Base


class Unit(Base):
    __tablename__ = "unit"
    id = Column(Integer, primary_key=True, unique=True, nullable=False)
    symbol = Column(String)
