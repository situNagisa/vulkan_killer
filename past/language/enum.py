import sys
import typing
from dataclasses import dataclass

from .specifier import typed, declared_type
from .name import name_introducer, name, depender, collect_depend_name_from_iterable


@dataclass
class enumerator:
    identifier: str
    value: str


@dataclass
class enum_specifier(typed, name_introducer, depender):
    from .keyword import enum as _enum
    from .name import name as _name
    
    key: _enum
    attribute: list[str]
    head_name: _name
    base: typing.Optional[declared_type]
    enumerator_list: typing.Optional[list[enumerator]]
    
    def introduced_name(self) -> _name:
        return self.head_name
    
    def get_depend_names(self) -> set[name]:
        result = set[name]()
        if self.base is not None and isinstance(self.base, declared_type):
            result = self.base.get_depend_names()
        if self.enumerator_list is not None:
            result = result | collect_depend_name_from_iterable(self.enumerator_list)
        return result
    
    def evaluate(self, index: int) -> int:
        e = self.enumerator_list[index]
        if e.value:
            return int(e.value)
        if index == 0:
            return 0
        return self.evaluate(index - 1) + 1
    
    def found_by_value(self, value: int) -> list[enumerator]:
        result = []
        for i, e in enumerate(self.enumerator_list):
            if value == self.evaluate(i):
                result.append(e)
        return result
    
    def min_enum(self) -> int:
        result = sys.maxsize
        for i in range(len(self.enumerator_list)):
            v = self.evaluate(i)
            if v < result:
                result = v
        return result