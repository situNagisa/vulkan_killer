import enum
import typing

import past.language as cpp
import past.language.declarator

from .name import identifier


class category(enum.Enum):
    none = -1
    typedef = 0
    class_ = 1
    enum = 2
    function = 3
    variable = 4
    
    def is_type(self) -> bool:
        return self in [category.typedef, category.class_, category.enum]
    
    def is_value(self) -> bool:
        return self in [category.function, category.variable]


def deduce_statement_category(s: cpp.statement.statement) -> category:
    if not isinstance(s, cpp.declaration.simple):
        return category.none
    if len(s.export_symbol_seq(None)) != 1:
        return category.none
    return deduce_symbol_category(s.export_symbol_seq(None)[0])


def deduce_symbol_category(s: cpp.symbol.symbol) -> category:
    if s.category == cpp.symbol.category.type:
        assert s.initializer is None
        if len(s.type_id.decl_specifier_seq) == 1 \
                and isinstance(s.type_id.decl_specifier_seq[0], cpp.name.name_introducer) \
                and s.type_id.decl_specifier_seq[0].introduced_name() == s.name:
            if isinstance(s.type_id.decl_specifier_seq[0], cpp.class_.class_):
                return category.class_
            if isinstance(s.type_id.decl_specifier_seq[0], cpp.enum.enum_specifier):
                return category.enum
            return category.none
        t = identifier(s.mangling.spelling)
        if t.bit or t.two:
            assert t.flag
        return category.typedef
    if s.category == cpp.symbol.category.value:
        if isinstance(s.type_id.declarator, cpp.function.function):
            return category.function
        if isinstance(s.type_id.declarator, cpp.declarator.abstract):
            return category.variable
    return category.none
