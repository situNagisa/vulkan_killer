import copy
import enum
import sys
import typing
from dataclasses import dataclass

from .name import name as _name
from .name import depender, collect_depend_name_from_iterable

class category(enum.Enum):
    type = 0
    value = 1
    
    def is_value(self) -> bool:
        return self == category.value
    
    def is_type(self) -> bool:
        return self == category.type


@dataclass
class symbol(depender):
    from .type import type_id as _type_id
    from .initialization import initializer as _initializer
    
    mangling: _name
    category: category
    type_id: _type_id
    name: _name
    initializer: typing.Optional[_initializer]
    
    def __init__(self,
                 type_id: _type_id,
                 category: category,
                 mangling: _name,
                 name: typing.Optional[_name] = None,
                 initializer: typing.Optional[_initializer] = None
                 ):
        self.mangling = copy.deepcopy(mangling)
        self.category = category
        self.type_id = type_id
        self.name = name if name is not None else mangling
        self.initializer = initializer
        
    def get_depend_names(self) -> set[_name]:
        result = self.type_id.get_depend_names()
        if self.initializer is not None and isinstance(self.initializer, depender):
            result = result | self.initializer.get_depend_names()
        return result

class symbol_sequence(list[symbol]):
    
    def __init__(self, data: list[symbol] = None):
        super().__init__(data or [])
    
    def __contains__(self, item: _name):
        return self[item] is not None
    
    def index(self, __value: _name, __start: int = 0, __stop: int = sys.maxsize) -> int:
        for i in range(__start, __stop):
            if self[i].mangling == __value:
                return i
        return -1
    
    def __getitem__(self, key: _name | int) -> typing.Optional[symbol]:
        if isinstance(key, int):
            return super().__getitem__(key)
        for i in self:
            if i.mangling == key:
                return i
        return None
    
    def __setitem__(self, key: _name | int, value: symbol):
        if isinstance(key, int):
            return super().__setitem__(key, value)
        assert key == value.mangling
        index = self.index(key)
        if index == -1:
            self.append(value)
            return
        super().__setitem__(index, value)
    
    def __delitem__(self, key: _name | int):
        if isinstance(key, int):
            return super().__delitem__(key)
        index = self.index(key)
        if index == -1:
            raise 'fuck you'
        super().__delitem__(index)
        raise 'fuck you'


symbol_table = typing.Callable[[_name], typing.Optional[symbol]]

class symbol_exporter:
    from abc import abstractmethod as _abstractmethod
    
    @_abstractmethod
    def export_symbol_seq(self, table: symbol_table) -> symbol_sequence:
        pass



