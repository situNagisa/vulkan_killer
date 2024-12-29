import copy
import logging

import past.language as cpp

import vk.lang.statement as vls
import vk.lang.name as vln
import vk.lang.category as vlc
from ..lang.module import key


def _create_constant(type_mangling: cpp.name.name, id: str, value: str) -> cpp.symbol.symbol:
    return cpp.symbol.symbol(
        type_id=cpp.type.type_id(decl_specifier_seq=[cpp.specifier.auto(),]),
        category=cpp.symbol.category.value,
        mangling=cpp.name.name(
            namespace=[''],
            spelling=id,
        ),
        initializer=cpp.initialization.copy(
            expression=cpp.expression.static_cast(
                cast_to=cpp.type.type_id(
                    decl_specifier_seq=[cpp.specifier.declared_type(name=copy.deepcopy(type_mangling)),],
                ),
                subexpression=cpp.expression.literal(
                    value_type=cpp.type.type_id(
                        decl_specifier_seq=[cpp.specifier.fundamental(
                            type=cpp.keyword.type.long,
                        )],
                    ),
                    value=value
                )
            )
        )
    )

def parse_c_program(module_keys: dict[cpp.name.name, key], p: dict[cpp.name.name, vls.vk]) -> dict[cpp.name.name, vls.plus_plus]:
    pfns: list[int] = []
    stmt_list: list[vls.plus_plus] = []
    for mangling, vk_stmt in p.items():
        location: cpp.location.source_location = vk_stmt.location
        symbol: cpp.symbol.symbol = vk_stmt.symbol
        c_c = vk_stmt.c_category
        trait = vln.identifier(symbol.mangling.spelling)
        
        if c_c == vlc.c_symbol.none:
            raise 'fuck you'
        
        if c_c in [
            vlc.c_symbol.flag_bit_v,
            vlc.c_symbol.flag64_bit_v,
            vlc.c_symbol.alias,
            vlc.c_symbol.using,
            vlc.c_symbol.flag,
            vlc.c_symbol.flag64,
            vlc.c_symbol.flag_bit,
            vlc.c_symbol.flag64_bit,
            vlc.c_symbol.struct,
        ]:
            new_symbol = copy.deepcopy(symbol)
            if c_c in [
                            vlc.c_symbol.flag_bit_v,
                            vlc.c_symbol.flag64_bit_v,
                        ]:
                new_symbol = _create_constant(symbol.type_id.decl_specifier_seq[0].name, symbol.name.spelling, symbol.initializer.expression.evaluate())
            stmt_list.append(vls.plus_plus(
                module_key=copy.deepcopy(module_keys[mangling]),
                mangling_category=vlc.mangling.none,
                cpp_category=vlc.cpp_symbol[c_c.name],
                symbol=new_symbol,
            ))
            continue
        if c_c == vlc.c_symbol.handle_struct:
            continue
        if c_c == vlc.c_symbol.handle:
            stmt_list.append(vls.plus_plus(
                module_key=copy.deepcopy(module_keys[mangling]),
                mangling_category=vlc.mangling.none,
                cpp_category=vlc.cpp_symbol.handle,
                symbol=cpp.symbol.symbol(
                    type_id=cpp.type.type_id(
                        decl_specifier_seq=[cpp.class_.class_(
                            class_key=cpp.keyword.class_.struct,
                            attribute=[],
                            head_name=cpp.name.name(
                                namespace=symbol.name.namespace,
                                spelling=symbol.name.spelling
                            ),
                            bases=[],
                            members=None,
                        )],
                        declarator=symbol.type_id.declarator
                    ),
                    category=symbol.category,
                    mangling=symbol.mangling,
                    name=symbol.name,
                )
            ))
            continue
        if c_c == vlc.c_symbol.enum:
            new = vls.plus_plus(
                module_key=copy.deepcopy(module_keys[mangling]),
                mangling_category=vlc.mangling.none,
                cpp_category=vlc.cpp_symbol.enum,
                symbol=copy.deepcopy(symbol),
            )
            stmt_list.append(new)
            spe = new.symbol.type_id.decl_specifier_seq[0]
            assert isinstance(spe, cpp.enum.enum_specifier)
            spe.key = cpp.keyword.enum.enum_class
            i = 0
            enumerators = []
            while i < len(spe.enumerator_list):
                e = spe.enumerator_list[i]
                from ..lang.name import enumerator
                e_t = enumerator(symbol.mangling.spelling, e.identifier)
                if trait.company == e_t.company and trait.ext == e_t.ext:
                    i += 1
                    continue
                enumerators.append(vls.plus_plus(
                module_key=copy.deepcopy(module_keys[mangling]),
                    mangling_category=vlc.mangling.none,
                    cpp_category=vlc.cpp_symbol.enumerator,
                    symbol=_create_constant(symbol.mangling, e.identifier, str(spe.evaluate(i)))
                ))
                del spe.enumerator_list[i]
            def sort_callback(s: vls.plus_plus):
                trait = vln.identifier(s.symbol.mangling.spelling)
                return trait.company
            
            stmt_list += list(sorted(enumerators, key=sort_callback))
            e = spe.enumerator_list[-1]
            from ..lang.name import enumerator
            e_t = enumerator(symbol.mangling.spelling, e.identifier)
            assert e_t.max_enum
            spe.base = tuple[int, int]((spe.evaluate(len(spe.enumerator_list) - 1), spe.min_enum()))
            del spe.enumerator_list[-1]
            continue
        if c_c == vlc.c_symbol.enum_bit:
            spe = symbol.type_id.decl_specifier_seq[0]
            assert isinstance(spe, cpp.enum.enum_specifier)
            from ..lang.name import enumerator
            e_t = enumerator(symbol.mangling.spelling, spe.enumerator_list[-1].identifier)
            assert e_t.max_enum
            max_enum = _create_constant(mangling, spe.enumerator_list[-1].identifier, str(spe.evaluate(len(spe.enumerator_list) - 1)))
            max_enum.mangling = mangling
            stmt_list.append(vls.plus_plus(
                module_key=copy.deepcopy(module_keys[mangling]),
                mangling_category=vlc.mangling.none,
                cpp_category=vlc.cpp_symbol.max_enum,
                symbol=max_enum,
            ))
            
            enumerators = []
            for i, e in enumerate(spe.enumerator_list[:-1]):
                enumerators.append(vls.plus_plus(
                    module_key=copy.deepcopy(module_keys[mangling]),
                    mangling_category=vlc.mangling.none,
                    cpp_category=vlc.cpp_symbol.flag_bit_v,
                    symbol=_create_constant(mangling, e.identifier, str(spe.evaluate(i)))
                ))
            def sort_callback(s: vls.plus_plus):
                trait = vln.enumerator(mangling.spelling, s.symbol.mangling.spelling)
                return trait.company
            stmt_list += list(sorted(enumerators, key=sort_callback))
        
        if c_c == vlc.c_symbol.pfn:
            pfns.append(len(stmt_list))
            stmt_list.append(vls.plus_plus(
                module_key=copy.deepcopy(module_keys[mangling]),
                mangling_category=vlc.mangling.none,
                cpp_category=vlc.cpp_symbol.pfn,
                symbol=copy.deepcopy(symbol),
            ))
            continue
        if c_c == vlc.c_symbol.function:
            pfn = None
            i = len(pfns)
            while i > 0:
                assert stmt_list[pfns[i - 1]].cpp_category == vlc.cpp_symbol.pfn
                pfn = stmt_list[pfns[i - 1]].symbol
                if pfn.name.spelling != f"PFN_{symbol.name.spelling}":
                    i -= 1
                    continue
                stmt_list[pfns[i - 1]] = vls.plus_plus(
                    module_key=copy.deepcopy(module_keys[mangling]),
                    mangling_category=vlc.mangling.none,
                    cpp_category=vlc.cpp_symbol.function,
                    symbol=copy.deepcopy(symbol)
                )
                stmt_list.append(vls.plus_plus(
                    module_key=copy.deepcopy(module_keys[mangling]),
                    mangling_category=vlc.mangling.none,
                    cpp_category=vlc.cpp_symbol.pfn_decl,
                    symbol=cpp.symbol.symbol(
                        type_id=cpp.type.type_id(
                            decl_specifier_seq=[cpp.specifier.decltype(
                                entry=mangling
                            )],
                            declarator=cpp.declarator.pointer(
                                attribute=[],
                                const=None,
                                volatile=None,
                                declarator=cpp.declarator.abstract()
                            )
                        ),
                        category=cpp.symbol.category.type,
                        mangling=copy.deepcopy(pfn.mangling)
                    )
                ))
                del pfns[i - 1]
                break
            assert pfn is not None
            continue
        
    result: dict[cpp.name.name, vls.plus_plus] = {}
    for s in stmt_list:
        if s.symbol.mangling not in result.keys():
            result[copy.deepcopy(s.symbol.mangling)] = s
            continue
        raise 'fuck you'
        
        
    return result
