from dataclasses import dataclass

from .declaration import block
from .name import name_introducer, depender, name
from .symbol import symbol_sequence, symbol, symbol_table
from .specifier import declared_type
from .type import type_id


@dataclass
class using(block, name_introducer, depender):
    from .name import name as _name
    
    namespace: list[str]
    identifier: _name
    
    def introduced_name(self) -> _name:
        from .name import name as _name
        return _name(
            namespace=self.namespace,
            spelling=self.identifier.spelling
        )
    
    def get_depend_names(self) -> set[_name]:
        return {self.identifier}
    
    def export_symbol_seq(self, table: symbol_table) -> symbol_sequence:
        ref_symbol = table(self.identifier)
        return symbol_sequence(data=[symbol(
            type_id=type_id(
                decl_specifier_seq=[declared_type(name=self.identifier)],
            ),
            category=ref_symbol.category,
            mangling=self.introduced_name(),
            name=self.introduced_name(),
            initializer=None,
        )])
