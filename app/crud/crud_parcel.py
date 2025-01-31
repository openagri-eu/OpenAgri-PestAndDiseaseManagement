from typing import List

from sqlalchemy.orm import Session

from crud.base import CRUDBase
from models import Parcel
from schemas import CreateParcel


class CrudParcel(CRUDBase[Parcel, CreateParcel, dict]):

    def get_all(self, db: Session) -> List[Parcel]:
        return db.query(Parcel).all()


parcel = CrudParcel(Parcel)