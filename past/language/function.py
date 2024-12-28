import copy
import typing
from dataclasses import dataclass

from .declarator import declarator as _declarator, copy_as_abstract_declarator
from .declarator import compound as _compound
from .name import name, depender, collect_depend_name_from_iterable


@dataclass
class parameter(depender):
    from .specifier import specifier as _specifier
    from .initialization import copy as _copy
    from .type import type_id as _type_id
    
    attribute: list[str]
    this: bool
    decl_specifier_seq: list[_specifier]
    declarator: _declarator
    initializer: typing.Optional[_copy]
    
    @property
    def type_id(self) -> _type_id:
        from .type import type_id as _type_id
        from .specifier_seq import cv_typed_only
        
        return _type_id(
            decl_specifier_seq=cv_typed_only(self.decl_specifier_seq),
            declarator=copy_as_abstract_declarator(copy.copy(self.declarator))
        )
    
    def get_depend_names(self) -> set[name]:
        result = collect_depend_name_from_iterable(self.decl_specifier_seq)
        if isinstance(self.declarator, depender):
            result = result | self.declarator.get_depend_names()
        if self.initializer is not None and isinstance(self.initializer, depender):
            result = result | self.initializer.get_depend_names()
        return result

@dataclass
class declarator(_declarator, _compound):
    from .cv import const as _const
    from .cv import volatile as _volatile
    from .name import name as _name
    
    declarator: _declarator
    parameter_list: list[parameter]
    const: typing.Optional[_const]
    volatile: typing.Optional[_volatile]
    # reference:
    noexcept: bool
    attribute: list[str]
    
    def introduced_name(self) -> _name:
        return self.declarator.introduced_name()
    
    def get_depend_names(self) -> set[name]:
        return super().get_depend_names() | collect_depend_name_from_iterable(self.parameter_list)
    
    def get_sub_declarator(self) -> _declarator:
        return self.declarator
    
    def set_sub_declarator(self, new: _declarator):
        self.declarator = new
    
    def __copy__(self):
        return declarator(
            declarator=copy.copy(self.declarator),
            parameter_list=self.parameter_list,
            const=self.const,
            volatile=self.volatile,
            noexcept=self.noexcept,
            attribute=[],
        )


class body:
    pass

class default(body):
    pass

@dataclass
class delete(body):
    why: str = ''
    
@dataclass
class normal_body(body):
    from .statement import compound as _compound
    # constructor initializer
    compound_statement: _compound

from .declaration import declaration as _declaration

@dataclass
class definition(_declaration):
    from .specifier import specifier as _specifier
    
    attribute: list[str]
    decl_specifier_seq: list[_specifier]
    declarator: declarator
    function_body: body