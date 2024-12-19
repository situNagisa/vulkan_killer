import copy
import typing
from dataclasses import dataclass
from abc import ABC

from .name import name_introducer

'''
declarator:
    abstract
    name
    pointer
    function
    array
'''


class declarator(ABC, name_introducer):
    pass


class compound:
    from abc import abstractmethod as _abstractmethod
    
    @_abstractmethod
    def get_sub_declarator(self) -> declarator:
        pass
    
    @_abstractmethod
    def set_sub_declarator(self, new: declarator):
        pass


class abstract(declarator):
    from .name import name as _name
    
    def introduced_name(self) -> _name:
        raise 'fuck you'


@dataclass
class name(declarator):
    from .name import name as _name
    identifier: _name
    
    def introduced_name(self) -> _name:
        return self.identifier


@dataclass
class pointer(declarator, compound):
    from .cv import const as _const
    from .cv import volatile as _volatile
    from .name import name as _name
    
    attribute: list[str]
    const: typing.Optional[_const]
    volatile: typing.Optional[_volatile]
    declarator: declarator
    
    def introduced_name(self) -> _name:
        return self.declarator.introduced_name()
    
    def get_sub_declarator(self) -> declarator:
        return self.declarator
    
    def set_sub_declarator(self, new: declarator):
        self.declarator = new
    
    def __copy__(self):
        return pointer(
            attribute=self.attribute,
            const=self.const,
            volatile=self.volatile,
            declarator=copy.copy(self.declarator)
        )


@dataclass
class array(declarator, compound):
    from .name import name as _name
    
    declarator: declarator
    count: int
    attribute: list[str]
    
    def introduced_name(self) -> _name:
        return self.declarator.introduced_name()
    
    def get_sub_declarator(self) -> declarator:
        return self.declarator
    
    def set_sub_declarator(self, new: declarator):
        self.declarator = new
    
    def __copy__(self):
        return array(
            declarator=copy.copy(self.declarator),
            count=self.count,
            attribute=self.attribute,
        )


def get_identifier_declarator(d: declarator) -> declarator:
    if not isinstance(d, compound):
        return d
    return get_identifier_declarator(d.get_sub_declarator())


def _replace_identifier_declarator_to(d: compound, new_identifier: declarator):
    assert not isinstance(new_identifier, compound)
    sub = d.get_sub_declarator()
    if isinstance(sub, compound):
        _replace_identifier_declarator_to(sub, new_identifier)
        return
    d.set_sub_declarator(new_identifier)


def copy_as_abstract_declarator(d: declarator) -> declarator:
    if isinstance(d, compound):
        result = copy.copy(d)
        _replace_identifier_declarator_to(result, abstract())
        return result
    return abstract()


from .name import name as _name


def rename_declarator(d: declarator, new_name: _name) -> declarator:
    if isinstance(d, compound):
        result = copy.copy(d)
        _replace_identifier_declarator_to(result, name(identifier=new_name))
        return result
    return name(identifier=new_name)
