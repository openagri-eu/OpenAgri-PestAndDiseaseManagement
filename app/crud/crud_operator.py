from typing import Optional

from sqlalchemy.orm import Session

from core.security import verify_password, get_password_hash
from crud.base import CRUDBase
from models import Operator
from schemas import OperatorAll


class CrudOperator(CRUDBase[Operator, OperatorAll, OperatorAll]):

    def get_all(self, db: Session):
        return db.query(Operator).all()


operator = CrudOperator(Operator)
