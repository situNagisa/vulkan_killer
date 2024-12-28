import copy

from past import language as cpp
import past.language.symbol
import past.language.statement
import past.language.name

from ..lang.statement import vk as vk_stmt

def collect_symbol_table(statements: list[cpp.statement.location_statement]) -> dict[cpp.name.name, vk_stmt]:
    result: dict[cpp.name.name, vk_stmt] = dict[cpp.name.name, vk_stmt]()
    
    def get_symbol_by_mangling(mangling: cpp.name.name) -> cpp.symbol.symbol:
        return result[mangling].symbol
    
    for location_statement in statements:
        extent = location_statement.extent
        statement = location_statement.stmt
        if not isinstance(statement, past.language.symbol.symbol_exporter):
            continue
        symbol_seq: past.language.symbol.symbol_sequence = statement.export_symbol_seq(get_symbol_by_mangling)
        for symbol in symbol_seq:
            if symbol.mangling not in result.keys():
                result[copy.deepcopy(symbol.mangling)] = vk_stmt(
                    location=cpp.location.source_location(
                        file=extent.file,
                        position=extent.start,
                    ),
                    symbol=symbol,
                )
                continue
            curr = result[symbol.mangling].symbol
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
            result[symbol.mangling] = vk_stmt(
                    location=cpp.location.source_location(
                        file=extent.file,
                        position=extent.start,
                    ),
                    symbol=symbol,
                )
    
    return result
