import copy
from abc import ABC
from dataclasses import dataclass

from .statement import statement
from .symbol import symbol_sequence, symbol_exporter
from .name import name, depender, collect_depend_name_from_iterable


class declaration(statement, symbol_exporter, depender, ABC):
    
    def get_depend_names(self) -> set[name]:
        return set[name]()


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
    
    def get_depend_names(self) -> set[name]:
        return collect_depend_name_from_iterable(self.decl_specifier_seq) | collect_depend_name_from_iterable(self.init_declarator_seq)
    
    def export_symbol_seq(self, table) -> symbol_sequence:
        from .type import type_id
        from .specifier_seq import cv_typed_only
        from .symbol import symbol, category
        from .declarator import copy_as_abstract_declarator
        from .name import name_introducer

        result: symbol_sequence = symbol_sequence()
        specifier_seq = cv_typed_only(self.decl_specifier_seq)
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
            from .enum import enum_specifier
            if not isinstance(specifier, enum_specifier):
                continue
            if specifier.enumerator_list is None or not len(specifier.enumerator_list):
                continue
            from .cv import const
            from .initialization import copy as copy_init
            from .expression import literal
            from .specifier import declared_type
            for i, enumerator in enumerate(specifier.enumerator_list):
                m = name(
                        namespace=specifier.introduced_name().namespace,
                        spelling=enumerator.identifier
                    )
                result.append(symbol(
                    type_id=type_id(decl_specifier_seq=[declared_type(name=copy.deepcopy(specifier.introduced_name())), const()]),
                    category=category.value,
                    mangling=copy.deepcopy(m),
                    name=copy.deepcopy(m),
                    initializer=copy_init(
                        expression=literal(
                            value_type=type_id(decl_specifier_seq=[declared_type(name=copy.deepcopy(m)), const()]),
                            value=f"{specifier.evaluate(i)}",
                        )
                    )
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
