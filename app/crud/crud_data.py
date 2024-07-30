from sqlalchemy.orm import Session

from crud.base import CRUDBase
from models import Data
from schemas import CreateData


class CrudData(CRUDBase[Data, CreateData, dict]):

    def get_all(self, db: Session):
        return db.query(CrudData).all()


data = CrudData(Data)
