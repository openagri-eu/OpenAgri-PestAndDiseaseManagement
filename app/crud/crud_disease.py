from sqlalchemy.orm import Session

from crud.base import CRUDBase
from models import Disease
from schemas import CreateDisease


class CrudDisease(CRUDBase[Disease, CreateDisease, dict]):

    def get_all(self, db: Session):
        response = db.query(Disease).all()

        return response


disease = CrudDisease(Disease)