from crud.base import CRUDBase
from models import Parcel
from schemas import CreateParcel


class CrudParcel(CRUDBase[Parcel, CreateParcel, dict]):
    pass


parcel = CrudParcel(Parcel)