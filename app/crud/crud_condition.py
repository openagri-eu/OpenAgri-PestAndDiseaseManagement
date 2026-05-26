from crud.base import CRUDBase
from models import Condition
from schemas import CreateCondition


class CrudCondition(CRUDBase[Condition, CreateCondition, dict]):
    pass


condition = CrudCondition(Condition)
