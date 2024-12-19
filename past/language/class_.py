import typing
from dataclasses import dataclass

from .specifier import specifier, declared_type, decltype, typed
from .name import name_introducer


@dataclass
class base_clause:
    from .keyword import access
    attribute: list[str]
    access_specifier: access
    virtual: bool
    class_or_computed: declared_type | decltype


@dataclass
class member:
    from .init_declarator import init_declarator as _init_declarator
    from .bit_field import bit_field as _bit_field
    attribute: list[str]
    decl_specifier_seq: list[specifier]
    member_declarator_seq: list[_init_declarator | _bit_field]
    

@dataclass
class class_(typed, name_introducer):
    from .keyword import class_ as _class
    from .name import name as _name
    class_key: _class
    attribute: list[str]
    head_name: _name
    bases: list[base_clause]
    members: typing.Optional[list[member]]
    
    def introduced_name(self) -> _name:
        return self.head_name
