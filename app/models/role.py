from typing import List

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship, Mapped

from db.base_class import Base


class Role(Base):
    __tablename__ = 'role'
    id = Column(Integer, primary_key=True, unique=True, nullable=False)
    name = Column(String, unique=True, nullable=False)

    users: Mapped[List["User"]] = relationship(back_populates="role")
