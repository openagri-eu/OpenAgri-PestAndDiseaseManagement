from crud.base import CRUDBase
from models import Rule
from schemas import CreateRule, UpdateRule


class CrudRule(CRUDBase[Rule, CreateRule, UpdateRule]):
    pass


rule = CrudRule(Rule)
