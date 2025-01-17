import typing
from dataclasses import dataclass

from .specifier import specifier, declared_type, decltype, typed
from .name import name_introducer, depender, collect_depend_name_from_iterable, name


@dataclass
class base_clause(depender):
    from .keyword import access as _access
    attribute: list[str]
    access_specifier: typing.Optional[_access]
    virtual: bool
    class_or_computed: declared_type | decltype
    
    def get_depend_names(self) -> set[name]:
        return self.class_or_computed.get_depend_names()
    


@dataclass
class member(depender):
    from .init_declarator import init_declarator as _init_declarator
    from .bit_field import bit_field as _bit_field
    attribute: list[str]
    decl_specifier_seq: list[specifier]
    member_declarator_seq: list[_init_declarator | _bit_field]
    
    def get_depend_names(self) -> set[name]:
        return collect_depend_name_from_iterable(self.decl_specifier_seq) | collect_depend_name_from_iterable(self.member_declarator_seq)
        
    

@dataclass
class class_(typed, name_introducer, depender):
    from .keyword import class_ as _class
    from .name import name as _name
    class_key: _class
    attribute: list[str]
    head_name: _name
    bases: list[base_clause]
    members: typing.Optional[list[member]]
    
    def introduced_name(self) -> _name:
        return self.head_name
    
    def get_depend_names(self) -> set[name]:
        result = collect_depend_name_from_iterable(self.bases)
        if self.members is not None:
            result = result | collect_depend_name_from_iterable(self.members)
        return result
