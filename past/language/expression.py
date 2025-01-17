import enum
import typing
from dataclasses import dataclass
from abc import ABC
from typing import TypeVar, Generic


class value_category(enum.Enum):
    pure_right = 0
    expiring = 1
    left = 2
    
    def is_general_left(self) -> bool:
        return self == value_category.left or self == value_category.expiring
    
    def is_right(self) -> bool:
        return self == value_category.pure_right or self == value_category.expiring


@dataclass
class expression:
    from abc import abstractmethod as _abstractmethod
    
    category: value_category
    
    # @_abstractmethod
    # @property
    # def type(self) -> _type_id:
    #     pass
    
    @_abstractmethod
    def evaluate(self):
        pass


@dataclass
class conversion(expression, ABC):
    pass


@dataclass
class static_cast(conversion):
    from .type import type_id as _type_id
    cast_to: _type_id
    subexpression: expression
    
    def __init__(self, cast_to: _type_id, subexpression: expression):
        super().__init__(category=value_category.pure_right)
        self.cast_to = cast_to
        self.subexpression = subexpression
    
    def evaluate(self):
        return self.subexpression.evaluate()

    @property
    def type(self):
        return self.cast_to
    

class primary(expression, ABC):
    pass


@dataclass
class literal(primary):
    from .type import type_id as _type_id
    value_type: _type_id
    value: str
    
    def __init__(self, value_type: _type_id, value: str):
        super().__init__(category=value_category.pure_right)
        self.value_type = value_type
        self.value = value
    
    def evaluate(self):
        return self.value
    
    @property
    def type(self) -> _type_id:
        return self.value_type
    

@dataclass
class identifier(primary):
    from .name import name as _name
    from .type import type_id as _type_id
    
    entry: _name
    
    def __init__(self, entry: _name):
        super().__init__(category=value_category.left)
        self.entry = entry
    
    def evaluate(self):
        return self.entry
    
    # @property
    # def type(self) -> _type_id:
    #     from ..algorithm import as_abstract_declarator
    #     from .type import type_id, as_typed_specifier_seq
    #
    #     # symbol = self.symbol_table[self.entry]
    #     raise 'fuck you'
        

