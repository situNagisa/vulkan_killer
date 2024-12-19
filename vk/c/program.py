import copy

import past.language.symbol
from past import language as cpp
import past.language.statement
import past.language.name

class program:
    statements: list[cpp.statement.statement]
    symbol_table: past.language.symbol.symbol_table
    
    def __init__(self, statements: list[cpp.statement.statement]):
        self.statements = statements
        self.symbol_table = _create_symbol_table(self.statements)
    
    def modify_symbol_table(self, new_symbols: past.language.symbol.symbol_sequence):
        _modify_symbol_table(self.symbol_table, new_symbols)
    
    def append_symbol(self, new_symbol: cpp.name.name_introducer):
        assert new_symbol.introduced_name() not in self.symbol_table.keys()
        self.symbol_table[copy.deepcopy(new_symbol.introduced_name())] = new_symbol
    
    def append_symbol_seq(self, new_symbols: past.language.symbol.symbol_sequence):
        for symbol in new_symbols:
            self.append_symbol(symbol)
    
def _modify_symbol_table(symbol_table: past.language.symbol.symbol_table, new_symbols: past.language.symbol.symbol_sequence):
    for new_symbol in new_symbols:
        assert new_symbol.introduced_name() in symbol_table.keys()
        symbol_table[new_symbol.introduced_name()] = new_symbol
        

def _create_symbol_table(statements: list[cpp.statement.statement]) -> past.language.symbol.symbol_table:
    result: past.language.symbol.symbol_table = past.language.symbol.symbol_table()
    for statement in statements:
        if not isinstance(statement, past.language.symbol.symbol_exporter):
            continue
        symbol_seq: past.language.symbol.symbol_sequence = statement.export_symbol_seq(result)
        for symbol in symbol_seq:
            if symbol.name not in result.keys():
                result[copy.deepcopy(symbol.name)] = symbol
                continue
            curr = result[symbol.name]
            assert curr.category == cpp.symbol.category.type
            assert curr.category == symbol.category
            if isinstance(curr.type_id.decl_specifier_seq[0], cpp.class_.class_):
                members = curr.type_id.decl_specifier_seq[0].members
            elif isinstance(curr.type_id.decl_specifier_seq[0], cpp.enum.enum_specifier):
                members = curr.type_id.decl_specifier_seq[0].enumerator_list
            else:
                raise 'fuck you'
            if members is not None:
                assert isinstance(symbol.type_id.decl_specifier_seq[0], cpp.specifier.elaborated_type)
                continue
            if isinstance(curr.type_id.decl_specifier_seq[0], cpp.class_.class_):
                assert isinstance(symbol.type_id.decl_specifier_seq[0], cpp.class_.class_)
            elif isinstance(curr.type_id.decl_specifier_seq[0], cpp.enum.enum_specifier):
                assert isinstance(symbol.type_id.decl_specifier_seq[0], cpp.enum.enum_specifier)
            result[symbol.name] = symbol
    
    return result
