from abc import ABC
from dataclasses import dataclass

from .statement import statement
from .symbol import symbol_sequence, symbol_exporter


class declaration(statement, symbol_exporter, ABC):
    pass


class block(declaration, ABC):
    pass


@dataclass
class simple(block):
    from .specifier import specifier as _specifier
    from .init_declarator import init_declarator as _init_declarator
    
    attribute: list[str]
    decl_specifier_seq: list[_specifier]
    init_declarator_seq: list[_init_declarator]
    
    def is_typedef_decl(self) -> bool:
        if not len(self.decl_specifier_seq):
            return False
        contains_typedef: bool = False
        for s in self.decl_specifier_seq:
            from .specifier import typedef, typed
            if isinstance(s, typedef):
                contains_typedef = True
                continue
            if not isinstance(s, typed):
                return False
        return contains_typedef
    
    def export_symbol_seq(self, table) -> symbol_sequence:
        from .type import type_id, as_typed_specifier_seq
        from .symbol import symbol, category
        from .declarator import copy_as_abstract_declarator
        from .name import name_introducer

        result: symbol_sequence = symbol_sequence()
        specifier_seq = as_typed_specifier_seq(self.decl_specifier_seq)
        symbol_category = category.type if self.is_typedef_decl() else category.value
        
        for specifier in specifier_seq:
            if not isinstance(specifier, name_introducer):
                continue
            result.append(symbol(
                type_id=type_id(decl_specifier_seq=[specifier]),
                category=category.type,
                mangling=specifier.introduced_name(),
                name=specifier.introduced_name(),
                initializer=None
            ))
        
        for init_declarator in self.init_declarator_seq:
            result.append(symbol(
                type_id=type_id(
                    decl_specifier_seq=specifier_seq,
                    declarator=copy_as_abstract_declarator(init_declarator.declarator)
                ),
                category=symbol_category,
                mangling=init_declarator.declarator.introduced_name(),
                name=init_declarator.declarator.introduced_name(),
                initializer=init_declarator.initializer
            ))
            
        return result
