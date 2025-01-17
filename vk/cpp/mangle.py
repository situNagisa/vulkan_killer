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


def _is_single_bit(num: int) -> bool:
    return num > 0 and (num & (num - 1)) == 0


def _countr_zero(num: int) -> int:
    return num.bit_length() - 1


def _is_int32_max(num: int) -> bool:
    return num == 0x7fffffff


def _std_int32_max() -> str:
    return '::std::numeric_limits<::std::int32_t>::max()'


def _mangle(api: str, vkpp_symbol: vls.plus_plus, table: cpp.symbol.symbol_table):
    mc = vkpp_symbol.mangling_category
    symbol = vkpp_symbol.symbol
    assert mc != category_mangling.none
    namespace: list[str] = copy.deepcopy(symbol.name.namespace)
    spelling: str = symbol.name.spelling
    if mc.is_enumerator():
        assert isinstance(symbol.initializer, cpp.initialization.copy)
        assert isinstance(symbol.initializer.expression, cpp.expression.static_cast)
        _spe = symbol.initializer.expression.cast_to.decl_specifier_seq[0]
        assert isinstance(_spe, cpp.specifier.declared_type)
        enum = table(_spe.name)
        trait = vk.lang.name.enumerator(enum.mangling.spelling, symbol.mangling.spelling)
    else:
        enum = None
        trait = vk.lang.name.identifier(symbol.mangling.spelling)
    
    # module
    assert vkpp_symbol.module_key.subcomponent == 'unknown'
    vkpp_symbol.module_key.subcomponent = 'function' if vkpp_symbol.cpp_category in [symbols.function, symbols.pfn_decl] else 'type'
    
    # name
    if trait.api.lower() == 'vk':
        namespace.append(api)
    else:
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
                assert not _is_int32_max(int(e.value))
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
    elif mc in [category_mangling.flag_bit, category_mangling.flag64_bit]:
        new_ns = _to_snake(trait.id)
        if mc == category_mangling.flag64_bit:
            new_ns += '64'
        new_ns += '_bits'
        namespace.append(new_ns)
        spelling = 'underlying_type'
    elif mc in [category_mangling.flag_bit_v, category_mangling.flag_bit_bit_v, category_mangling.flag_bit_none_v]:
        namespace.append(enum.name.namespace[-1])
        match mc:
            case category_mangling.flag_bit_v:
                spelling = _to_snake(trait.id) + '_'
            case category_mangling.flag_bit_bit_v:
                spelling = _to_snake(trait.id)
            case category_mangling.flag_bit_none_v:
                spelling = 'none'
        if symbol.initializer is not None:
            static_cast = symbol.initializer.expression
            assert isinstance(static_cast, cpp.expression.static_cast)
            literal = static_cast.subexpression
            assert isinstance(literal, cpp.expression.literal)
            literal.value = literal.value.lower()
            literal.value = literal.value.removesuffix('ull')
            if literal.value.startswith('0x'):
                v = int(literal.evaluate(), 16)
            else:
                v = int(literal.evaluate())
            literal.value = f"1ull << {_countr_zero(v)}" if _is_single_bit(v) else hex(v).lower()
    
    elif mc == category_mangling.alias:
        spelling = _to_snake(trait.id)
        spe = symbol.type_id.decl_specifier_seq[0]
        if isinstance(spe, cpp.specifier.declared_type):
            if len(spe.name.namespace) < 2 or spe.name.namespace[:2] != ['', 'std']:
                ref_trait = vk.lang.name.identifier(spe.name.spelling)
                if ref_trait.id == trait.id:
                    ref_symbol = table(spe.name)
                    ref_spe = ref_symbol.type_id.decl_specifier_seq[0]
                    if isinstance(ref_spe, cpp.enum.enum_specifier):
                        spelling += '_' + trait.company.lower()
    
    elif mc == category_mangling.struct:
        spelling = _to_snake(trait.id)
        spe = symbol.type_id.decl_specifier_seq[0]
        assert isinstance(spe, cpp.class_.class_)
        for member in spe.members:
            for declarator in member.member_declarator_seq:
                if isinstance(declarator, cpp.init_declarator.init_declarator):
                    member_spelling = declarator.declarator.introduced_name().spelling
                    member_trait = vk.lang.name.variable(member_spelling)
                elif isinstance(declarator, cpp.bit_field.bit_field):
                    member_spelling = declarator.identifier
                    member_trait = vk.lang.name.variable(member_spelling)
                else:
                    raise 'fuck you'
                if member_spelling == 'sType':
                    member_spelling = '_structure_type'
                elif member_spelling == 'pNext':
                    member_spelling = 'structure_next'
                else:
                    member_spelling = _to_snake(member_trait.id)
                    if member_trait.prefix and member_trait.prefix != 'pfn' and member_trait.prefix[0] == 'p':
                        member_spelling += '_ptr' * (len(member_trait.prefix) - 1)
                    if member_spelling == spelling:
                        member_spelling += '_'
                    spe = member.decl_specifier_seq[0]
                    if isinstance(spe, cpp.specifier.declared_type) and not spe.name.qualified_name.startswith('::std::'):
                        ref_symbol = table(spe.name)
                        if member_spelling == ref_symbol.name.spelling:
                            member_spelling += '_'
                if isinstance(declarator, cpp.init_declarator.init_declarator):
                    declarator.declarator.introduced_name().spelling = member_spelling
                elif isinstance(declarator, cpp.bit_field.bit_field):
                    declarator.identifier = member_spelling
                else:
                    raise 'fuck you'
    
    elif mc == category_mangling.handle:
        namespace.append('handle')
        spelling = _to_snake(trait.id)
        spe = symbol.type_id.decl_specifier_seq[0]
        assert isinstance(spe, cpp.class_.class_)
        spe.head_name.spelling = '_' + spelling
    
    elif mc.is_using():
        spe = symbol.type_id.decl_specifier_seq[0]
        assert isinstance(spe, cpp.specifier.declared_type)
        ref_symbol = table(spe.name)
        spelling = ref_symbol.name.spelling
        if trait.company and isinstance(ref_symbol.type_id.decl_specifier_seq[0], cpp.enum.enum_specifier):
            spelling += '_' + trait.company.lower()
        
        match mc:
            case category_mangling.using_flag_bit:
                namespace.append(_to_snake(trait.id) + '_bits')
            case category_mangling.using_flag64_bit:
                namespace.append(_to_snake(trait.id) + '64_bits')
            case _:
                pass
    
    spelling = _preventing_name_collisions(spelling)
    
    vkpp_symbol.symbol.name.spelling = spelling
    vkpp_symbol.symbol.name.namespace = namespace


def _classify(category: symbols, symbol: cpp.symbol.symbol, table: cpp.symbol.symbol_table) -> category_mangling:
    assert category != symbols.none
    
    if category.is_enumerator():
        assert isinstance(symbol.initializer, cpp.initialization.copy)
        assert isinstance(symbol.initializer.expression, cpp.expression.static_cast)
        spe = symbol.initializer.expression.cast_to.decl_specifier_seq[0]
        assert isinstance(spe, cpp.specifier.declared_type)
        enum = table(spe.name)
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
    if category in [symbols.enumerator, symbols.inner_enumerator]:
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


def mangle(api: str, program: dict[cpp.name.name, vls.plus_plus]):
    def get_symbol_by_mangling(m: cpp.name.name) -> cpp.symbol.symbol:
        return program[m].symbol
        
    for mangling, vs in program.items():
        vs.mangling_category = _classify(vs.cpp_category, vs.symbol, get_symbol_by_mangling)
        _mangle(api, vs, get_symbol_by_mangling)
