import copy

import past.language as cpp
import past.language.symbol
import past.language.declaration
import past.language.type_alias
import past.language.init_declarator

import vk.lang.statement as vls
from vk.lang.category import mangling as category_mangling
from vk.lang.category import cpp_symbol as symbols
import vk.lang.name
from ..ccpp import is_cpp_keyword


def _to_snake(words: list[str]) -> str:
    return '_'.join([word.lower() for word in words])


def _preventing_name_collisions(spelling: str) -> str:
    if spelling and spelling[0].isdigit():
        return f"_{spelling}"
    
    if is_cpp_keyword(spelling):
        return f"{spelling}_"
    
    return spelling


def _mangle(mc: category_mangling, symbol: cpp.symbol.symbol, table: cpp.symbol.symbol_table) -> cpp.name.name:
    assert mc != category_mangling.none
    namespace: list[str] = copy.deepcopy(symbol.name.namespace)
    spelling: str = symbol.name.spelling
    if mc.is_enumerator():
        assert isinstance(symbol.initializer, cpp.initialization.copy)
        assert isinstance(symbol.initializer.expression, cpp.expression.static_cast)
        _spe = symbol.initializer.expression.cast_to.decl_specifier_seq[0]
        assert isinstance(_spe, cpp.specifier.declared_type)
        enum = table[_spe.name]
        trait = vk.lang.name.enumerator(enum.mangling.spelling, symbol.mangling.spelling)
    else:
        enum = None
        trait = vk.lang.name.identifier(symbol.mangling.spelling)
    
    namespace.append(trait.api.lower())
    if trait.company:
        namespace.append(trait.company.lower())
    if trait.ext:
        namespace.append('ext')
    
    if mc == category_mangling.function:
        namespace.append('c')
    elif mc == category_mangling.function_ptr_decl:
        namespace.append('c')
        spelling = _to_snake(trait.id)
    elif mc == category_mangling.function_ptr:
        spelling = _to_snake(trait.id)
    
    elif mc == category_mangling.enum:
        spelling = _to_snake(trait.id)
        
        spe = symbol.type_id.decl_specifier_seq[0]
        assert isinstance(spe, cpp.enum.enum_specifier)
        prev = -1
        for e_i, e in enumerate(spe.enumerator_list):
            e_t = vk.lang.name.enumerator(symbol.mangling.spelling, e.identifier)
            e.identifier = 'none' if e_t.none else _to_snake(e_t.id)
            e.identifier = _preventing_name_collisions(e.identifier)
            
            if not e.value:
                prev += 1
                continue
            v = spe.evaluate(e_i)
            if v == prev + 1:
                e.value = ''
                prev += 1
            else:
                prev = v
    elif mc == category_mangling.enumerator:
        namespace.append(enum.name.spelling)
        spelling = _to_snake(trait.id)
    elif mc == category_mangling.enumerator_none:
        namespace.append(enum.name.spelling)
        spelling = 'none'
    
    elif mc == category_mangling.flag:
        spelling = _to_snake(trait.id) + '_flag'
    elif mc == category_mangling.flag64:
        spelling = _to_snake(trait.id) + '_flag64'
    elif mc == category_mangling.flag_bit:
        namespace.append(_to_snake(trait.id) + '_bits')
        spelling = 'underlying_type'
    elif mc == category_mangling.flag64_bit:
        namespace.append(_to_snake(trait.id) + '64_bits')
        spelling = 'underlying_type'
    elif mc == category_mangling.flag_bit_v:
        namespace.append(enum.name.namespace[-1])
        spelling = _to_snake(trait.id) + '_'
    elif mc == category_mangling.flag_bit_bit_v:
        namespace.append(enum.name.namespace[-1])
        spelling = _to_snake(trait.id)
    elif mc == category_mangling.flag_bit_none_v:
        namespace.append(enum.name.namespace[-1])
        spelling = 'none'
    
    elif mc == category_mangling.alias:
        spelling = _to_snake(trait.id)
    
    elif mc == category_mangling.struct:
        spelling = _to_snake(trait.id)
    
    elif mc == category_mangling.handle:
        namespace.append('handle')
        spelling = _to_snake(trait.id)
        spe = symbol.type_id.decl_specifier_seq[0]
        assert isinstance(spe, cpp.class_.class_)
        spe.head_name.spelling = '_' + spelling
    
    elif mc.is_using():
        spe = symbol.type_id.decl_specifier_seq[0]
        assert isinstance(spe, cpp.specifier.declared_type)
        ref_symbol = table[spe.name]
        spelling = ref_symbol.name.spelling
        
        match mc:
            case category_mangling.using_flag_bit:
                namespace.append(_to_snake(trait.id) + '_bits')
            case category_mangling.using_flag64_bit:
                namespace.append(_to_snake(trait.id) + '64_bits')
    
    spelling = _preventing_name_collisions(spelling)
    
    return cpp.name.name(
        namespace=namespace,
        spelling=spelling,
    )


def _classify(category: symbols, symbol: cpp.symbol.symbol, table: cpp.symbol.symbol_table) -> category_mangling:
    assert category != symbols.none
    
    if category.is_enumerator():
        assert isinstance(symbol.initializer, cpp.initialization.copy)
        assert isinstance(symbol.initializer.expression, cpp.expression.static_cast)
        spe = symbol.initializer.expression.cast_to.decl_specifier_seq[0]
        assert isinstance(spe, cpp.specifier.declared_type)
        enum = table[spe.name]
        enum_trait = vk.lang.name.identifier(enum.mangling.spelling)
        trait = vk.lang.name.enumerator(enum.mangling.spelling, symbol.mangling.spelling)
    else:
        trait = vk.lang.name.identifier(symbol.mangling.spelling)
    
    if category == symbols.function:
        return category_mangling.function
    if category == symbols.pfn_decl:
        return category_mangling.function_ptr_decl
    if category == symbols.pfn:
        return category_mangling.function_ptr
    
    if category in [symbols.flag_bit_v, symbols.flag64_bit_v]:
        if trait.none:
            return category_mangling.flag_bit_none_v
        if trait.bit:
            return category_mangling.flag_bit_bit_v
        return category_mangling.flag_bit_v
    if category == symbols.enumerator:
        if trait.none:
            return category_mangling.enumerator_none
        return category_mangling.enumerator
    if category == symbols.max_enum:
        return category_mangling.flag_bit
    
    if category == symbols.handle:
        return category_mangling.handle
    
    if category == symbols.alias:
        return category_mangling.alias
    
    if category == symbols.struct:
        return category_mangling.struct
    
    if category == symbols.enum:
        return category_mangling.enum
    
    if category == symbols.using:
        if trait.bit:
            return category_mangling.using_flag64_bit if trait.two else category_mangling.using_flag_bit
        else:
            return category_mangling.using
    
    if category == symbols.flag:
        return category_mangling.flag
    if category == symbols.flag64:
        return category_mangling.flag64
    if category == symbols.flag_bit:
        return category_mangling.flag_bit
    if category == symbols.flag64_bit:
        return category_mangling.flag64_bit
    
    raise 'fuck you'


def mangle(program: dict[cpp.name.name, vls.statement]):
    symbol_table: dict[cpp.name.name, cpp.symbol.symbol] = {}
    for mangling, vs in program.items():
        symbol_table[mangling] = vs.symbol
    for mangling, vs in program.items():
        mc = _classify(vs.category, vs.symbol, symbol_table)
        new_name = _mangle(mc, vs.symbol, symbol_table)
        vs.symbol.name.namespace = new_name.namespace
        vs.symbol.name.spelling = new_name.spelling


def __mangle(vs: vls.statement, symbol_table: dict[cpp.name.name, cpp.symbol.symbol]):
    category = vs.category
    symbol = vs.symbol
    
    assert category != symbols.none
    
    if category.is_enumerator():
        assert isinstance(symbol.initializer, cpp.initialization.copy)
        assert isinstance(symbol.initializer.expression, cpp.expression.static_cast)
        spe = symbol.initializer.expression.cast_to.decl_specifier_seq[0]
        assert isinstance(spe, cpp.specifier.declared_type)
        enum = symbol_table[spe.name]
        enum_trait = vk.lang.name.identifier(enum.mangling.spelling)
        trait = vk.lang.name.enumerator(enum.mangling.spelling, symbol.mangling.spelling)
        
        symbol.name.namespace = ['', trait.api.lower()]
        if enum_trait.company != trait.company:
            # assert not enum_trait.company
            symbol.name.namespace.append(trait.company.lower())
        if enum_trait.ext != trait.ext:
            assert not enum_trait.ext
            symbol.name.namespace.append('ext')
        if category in [symbols.enumerator]:
            symbol.name.namespace.append(enum.name.spelling)
        else:
            symbol.name.namespace.append(enum.name.namespace[-1])
        
        if trait.none:
            if enum_trait.flag:
                assert enum_trait.bit
            symbol.name.spelling = 'none'
        else:
            symbol.name.spelling = _to_snake(trait.id)
            if enum_trait.flag and not trait.bit:
                symbol.name.spelling += '_'
        
        if symbol.name.spelling[0].isdigit():
            symbol.name.spelling = '_' + symbol.name.spelling
        elif is_cpp_keyword(symbol.name.spelling):
            symbol.name.spelling = symbol.name.spelling + '_'
    else:
        trait = vk.lang.name.identifier(symbol.mangling.spelling)
        symbol.name.spelling = _to_snake(trait.id)
        symbol.name.namespace = ['', trait.api.lower()]
        if trait.company:
            symbol.name.namespace.append(trait.company.lower())
        if trait.ext:
            symbol.name.namespace.append('ext')
        
        if category in [symbols.function, symbols.pfn_decl]:
            symbol.name.namespace.append('c')
            if category == symbols.function:
                symbol.name.spelling = symbol.mangling.spelling
            # elif category == symbols.pfn_decl:
            #     symbol.name.spelling += '_ptr_t'
        elif category in [symbols.max_enum, symbols.flag_bit, symbols.flag64_bit, symbols.using]:
            symbol.name.namespace.append(_to_snake(trait.id) + ('_64' if trait.two else '') + '_bits')
            symbol.name.spelling = 'underlying_type'
        elif category in [symbols.flag64]:
            symbol.name.spelling += '_64'
        elif category == symbols.handle:
            symbol.name.spelling += '_handle'
        elif category in [symbols.enum]:
            spe = symbol.type_id.decl_specifier_seq[0]
            assert isinstance(spe, cpp.enum.enum_specifier)
            prev = -1
            for e_i, e in enumerate(spe.enumerator_list):
                e_t = vk.lang.name.enumerator(symbol.mangling.spelling, e.identifier)
                if e_t.none:
                    e.identifier = 'none'
                else:
                    e.identifier = _to_snake(e_t.id)
                    if e.identifier and e.identifier[0].isdigit():
                        e.identifier = '_' + e.identifier
                    elif is_cpp_keyword(e.identifier):
                        e.identifier = e.identifier + '_'
                if not e.value:
                    prev += 1
                    continue
                if spe.evaluate(e_i) == prev + 1:
                    e.value = ''
                    prev += 1
                else:
                    prev = spe.evaluate(e_i)
