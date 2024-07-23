from sqlalchemy import Column, Integer, String

from db.base_class import Base


class Operator(Base):
    __tablename__ = "operator"
    id = Column(Integer, primary_key=True, unique=True, nullable=False)
    operator = Column(String)
