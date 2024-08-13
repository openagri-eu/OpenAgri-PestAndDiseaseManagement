import traceback

from fastapi.encoders import jsonable_encoder
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from crud.base import CRUDBase, CreateSchemaType, ModelType
from models import Condition
from schemas import CreateCondition


class CrudCondition(CRUDBase[Condition, CreateCondition, dict]):

    def get_all(self, db: Session):
        return db.query(Condition).all()


condition = CrudCondition(Condition)
