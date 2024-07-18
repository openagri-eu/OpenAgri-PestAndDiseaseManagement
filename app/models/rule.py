from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import mapped_column, Mapped, relationship

from db.base_class import Base
from .action import Action


class Rule(Base):
    __tablename__ = "rule"
    id = Column(Integer, primary_key=True, unique=True, nullable=False)
    name = Column(String)
    description = Column(String, nullable=True)

    # action_id: Mapped[int] = mapped_column(ForeignKey("action.id"))
    # action: Mapped["Action"] = relationship(back_populates="users")
