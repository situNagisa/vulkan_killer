import copy
import typing
from dataclasses import dataclass

from .declarator import declarator as _declarator, copy_as_abstract_declarator
from .declarator import compound as _compound


@dataclass
class parameter:
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
        from .type import type_id as _type_id, as_typed_specifier_seq
        
        return _type_id(
            decl_specifier_seq=as_typed_specifier_seq(self.decl_specifier_seq),
            declarator=copy_as_abstract_declarator(copy.copy(self.declarator))
        )

@dataclass
class function(_declarator, _compound):
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
    
    def get_sub_declarator(self) -> _declarator:
        return self.declarator
    
    def set_sub_declarator(self, new: _declarator):
        self.declarator = new
    
    def __copy__(self):
        return function(
            declarator=copy.copy(self.declarator),
            parameter_list=self.parameter_list,
            const=self.const,
            volatile=self.volatile,
            noexcept=self.noexcept,
            attribute=[],
        )
