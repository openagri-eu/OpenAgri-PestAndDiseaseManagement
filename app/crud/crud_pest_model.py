from typing import Optional

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from crud.base import CRUDBase

from models import PestModel, Cultivation
from schemas import CreatePestModel, UpdatePestModel


class CrudPestModel(CRUDBase[PestModel, CreatePestModel, UpdatePestModel]):

    def create(self, db: Session, obj_in: CreatePestModel, **kwargs) -> Optional[PestModel]:

        pest_model_db = PestModel(name=obj_in.name, description=obj_in.description, geo_areas_of_application=obj_in.geo_areas_of_application)

        db.add(pest_model_db)
        try:
            db.commit()
        except SQLAlchemyError:
            db.rollback()
            return None
        db.refresh(pest_model_db)

        cultivations = [Cultivation(name=x, pest_model_id=pest_model_db.id) for x in obj_in.cultivations]

        db.add_all(cultivations)
        try:
            db.commit()
        except SQLAlchemyError:
            db.rollback()

            db.delete(pest_model_db)
            try:
                db.commit()
            except SQLAlchemyError:
                return None

            return None

        for c in cultivations:
            db.refresh(c)

        db.refresh(pest_model_db)

        return pest_model_db



pest_model = CrudPestModel(PestModel)
