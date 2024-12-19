import typing

import past.language as cpp
import past.language.symbol
import past.language.declaration
import past.language.type_alias
import past.language.init_declarator
import past.language.using_declaration

from vk.coder import code as _code
from vk.namespace import node
import vk.lang.statement as vls
import vk.lang.category as vlc


def _create_statement_from_vs(vs: vls.statement) -> cpp.declaration.declaration:
    category = vs.category
    symbol = vs.symbol
    symbols = vlc.cpp_symbol
    assert category != symbols.none
    
    
    if category.is_value():
        attributes: list[str] = []
        if category == symbols.function:
            ext_specifiers = [cpp.specifier.storage_class.extern_c]
        # elif category in [symbols.flag_bit_v, symbols.flag64_bit_v]:
        else:
            ext_specifiers = [
                cpp.specifier.inline(),
                cpp.specifier.compile_time.constexpr,
            ]
        return cpp.declaration.simple(
            attribute=attributes,
            decl_specifier_seq=ext_specifiers + symbol.type_id.decl_specifier_seq,
            init_declarator_seq=[cpp.init_declarator.init_declarator(
                declarator=cpp.declarator.rename_declarator(symbol.type_id.declarator, symbol.name),
                initializer=symbol.initializer
            )],
        )
    if category.is_type():
        if category in [symbols.struct, symbols.enum]:
            return cpp.declaration.simple(
                attribute=[],
                decl_specifier_seq=symbol.type_id.decl_specifier_seq,
                init_declarator_seq=[]
            )
        if category in [symbols.using]:
            return cpp.using_declaration.using(
                namespace=symbol.name.namespace,
                identifier=symbol.type_id.decl_specifier_seq[0].name
            )
        result = cpp.type_alias.alias(
                                            identifier=symbol.name,
                                            attribute=[],
                                            type_id=symbol.type_id,
                                        )
        return result
        

def generate(program: dict[cpp.name.name, vls.statement]):
    coder = _code()
    root = node('')
    
    def relative_name(name: cpp.name.name) -> str:
        target_ns: list[str] = name.namespace + [name.spelling]
        base = cpp.name.base_namespace(target_ns, coder.ns)
        count = base
        rn = target_ns[count:]
        if base == len(coder.ns):
            return cpp.name.relative_name(name, coder.ns)
        
        while True:
            actual = root.find_namespace_on(coder.ns, [rn[0]])
            if actual + rn == target_ns:
                break
            assert count > 0
            count -= 1
            rn = target_ns[count:]
            
        if count == 0 or count == 1:
            return name.qualified_name
        assert rn[-1] == name.spelling
        return cpp.name.qualified_name(name.spelling, rn[:-1])
    
    symbol_table: dict[cpp.name.name, cpp.symbol.symbol] = {}
    for mangling, vs in program.items():
        symbol_table[mangling] = vs.symbol
    
    for mangling, vs in program.items():
        category: vlc.cpp_symbol = vs.category
        symbol: cpp.symbol.symbol = vs.symbol
        
        coder.change_namespace(symbol.name.namespace)
        curr = root
        for ns in symbol.name.namespace[1:] + [symbol.name.spelling]:
            if ns not in curr:
                curr.add(node(ns))
            curr = curr[ns]
        
        assert category != vlc.cpp_symbol.none
        
        if category == vlc.cpp_symbol.max_enum:
            assert isinstance(symbol.initializer, cpp.initialization.copy)
            coder.write_line(f"using underlying_type = _calculate_enum_underlying_type_t<{symbol.initializer.expression.evaluate()}>;")
            continue
        
        coder.write_line(_generate_statement(_create_statement_from_vs(vs), relative_name, symbol_table))

    coder.change_namespace([''])
    return coder.data


relative_name_t = typing.Callable[[cpp.name.name], str]


def _cat_str(*s: str) -> str:
    s = list(filter(lambda ss: ss != '', s))
    if not len(s):
        return ''
    result = s[0]
    for ss in s[1:]:
        if not ss:
            continue
        result += ' ' + ss
    return result


def _generate_type(t: cpp.type.type_id, relative_name: relative_name_t,
                   table: past.language.symbol.symbol_table) -> str:
    if isinstance(t, cpp.type.type_id):
        return _cat_str(
            _generate_specifier_seq(t.decl_specifier_seq, relative_name, table),
            _generate_declarator(t.declarator, relative_name, table),
        )
    raise 'fuck you'


def _generate_statement(s: cpp.statement.statement, relative_name: relative_name_t,
                        table: past.language.symbol.symbol_table) -> str:
    if isinstance(s, cpp.declaration.declaration):
        if isinstance(s, cpp.declaration.block):
            if isinstance(s, cpp.declaration.simple):
                return _cat_str(
                    _generate_specifier_seq(s.decl_specifier_seq, relative_name, table),
                    _generate_init_declarator_seq(s.init_declarator_seq, relative_name, table),
                ) + ';'
            if isinstance(s, cpp.type_alias.alias):
                return _cat_str(
                    'using',
                    s.identifier.spelling,
                    '=',
                    _generate_type(s.type_id, relative_name, table),
                ) + ';'
            if isinstance(s, cpp.using_declaration.using):
                return _cat_str(
                    'using',
                    # relative_name(table[s.identifier].name)
                    table[s.identifier].name.qualified_name
                ) + ';'
    raise 'fuck you'


def _generate_specifier_seq(ss: list[cpp.specifier.specifier], relative_name: relative_name_t,
                            table: past.language.symbol.symbol_table) -> str:
    return ' '.join([_generate_specifier(s, relative_name, table) for s in ss])


def _generate_specifier(s: cpp.specifier.specifier, relative_name: relative_name_t,
                        table: past.language.symbol.symbol_table) -> str:
    if isinstance(s, cpp.keyword.keyword) and not isinstance(s, cpp.specifier.decltype):
        return s.name
    if isinstance(s, cpp.specifier.typed):
        if isinstance(s, cpp.specifier.fundamental):
            return s.type if isinstance(s.type, str) else s.type.name
        if isinstance(s, cpp.specifier.decltype):
            result = f"{s.name}"
            assert s.entry in table.keys()
            d = table[s.entry]
            result += f"({relative_name(d.name)})"
            return result
        if isinstance(s, cpp.specifier.declared_type):
            if len(s.name.namespace) == 2 and s.name.namespace[0] == '' and s.name.namespace[1] == 'std':
                return s.name.qualified_name
            assert s.name in table.keys()
            d = table[s.name]
            return f"{relative_name(d.name)}"
        if isinstance(s, cpp.specifier.elaborated_type):
            return _cat_str(s.key.name, _generate_specifier(s.identifier, relative_name, table))
        if isinstance(s, cpp.class_.class_):
            result = _cat_str(s.class_key.name, s.head_name.spelling)
            if s.members is not None:
                result += '\n{\n' if len(s.members) else '{'
                for member in s.members:
                    result += f'\t{_generate_specifier_seq(member.decl_specifier_seq, relative_name, table)}'
                    if len(member.member_declarator_seq):
                        result += ' '
                    
                    def generate_member_ds(ds: cpp.init_declarator.init_declarator | cpp.bit_field.bit_field) -> str:
                        if isinstance(ds, cpp.init_declarator.init_declarator):
                            return _generate_init_declarator(ds, relative_name, table)
                        return _cat_str(ds.identifier, ':', ds.width,
                                        '' if not ds.initializer else _generate_initializer(ds.initializer,
                                                                                            relative_name,
                                                                                            table))
                    
                    result += ', '.join(generate_member_ds(d) for d in member.member_declarator_seq)
                    result += ';\n'
                result += '}'
            return result
        if isinstance(s, cpp.enum.enum_specifier):
            result = _cat_str(s.key.name, s.head_name.spelling)
            if s.base is not None:
                assert isinstance(s.base, tuple)
                result = _cat_str(result, ':', f"_calculate_enum_underlying_type_t<{s.base[0]}, {s.base[1]}>")
            if s.enumerator_list is not None:
                result += '\n{\n' if len(s.enumerator_list) else '{'
                for enumerator in s.enumerator_list:
                    result += f"\t{enumerator.identifier}"
                    if enumerator.value:
                        result += f" = {enumerator.value}"
                    result += f",\n"
                result += '}'
            return result
    raise 'fuck you'


def _generate_init_declarator(d: cpp.init_declarator.init_declarator, relative_name: relative_name_t,
                              table: past.language.symbol.symbol_table) -> str:
    return _cat_str(
        _generate_declarator(d.declarator, relative_name, table),
        _generate_initializer(d.initializer, relative_name, table) if d.initializer is not None else ''
    )


def _generate_init_declarator_seq(d: list[cpp.init_declarator.init_declarator], relative_name: relative_name_t,
                                  table: past.language.symbol.symbol_table) -> str:
    return ', '.join([_generate_init_declarator(dd, relative_name, table) for dd in d])


def _generate_expression(e: cpp.expression.expression, relative_name: relative_name_t,
                         table: past.language.symbol.symbol_table) -> str:
    if isinstance(e, cpp.expression.primary):
        if isinstance(e, cpp.expression.literal):
            return str(e.value)
        if isinstance(e, cpp.expression.identifier):
            symbol = table[e.entry]
            assert isinstance(symbol, cpp.declarator.declarator)
            return relative_name(symbol.introduced_name())
        raise 'fuck you'
    if isinstance(e, cpp.expression.conversion):
        if isinstance(e, cpp.expression.static_cast):
            return f"static_cast<{_generate_type(e.cast_to, relative_name, table)}>({_generate_expression(e.subexpression, relative_name, table)})"
    
    raise 'fuck you'


def _generate_initializer(i: cpp.initialization.initializer, relative_name: relative_name_t,
                          table: past.language.symbol.symbol_table) -> str:
    if isinstance(i, cpp.initialization.copy):
        return _cat_str(
            '=',
            _generate_expression(i.expression, relative_name, table)
        )
    raise 'fuck you'


def _generate_declarator(d: cpp.declarator.declarator, relative_name: relative_name_t,
                         table: past.language.symbol.symbol_table) -> str:
    if isinstance(d, cpp.declarator.abstract):
        return ''
    if isinstance(d, cpp.declarator.name):
        return d.identifier.spelling  # relative_name(d.identifier)
    if isinstance(d, cpp.declarator.pointer):
        return '*' + _cat_str(
            d.const.name if d.const else '',
            d.volatile.name if d.volatile else '',
            _generate_declarator(d.get_sub_declarator(), relative_name, table)
        )
    if isinstance(d, cpp.declarator.array):
        result = f"{_generate_declarator(d.get_sub_declarator(), relative_name, table)}"
        if isinstance(d.get_sub_declarator(), cpp.declarator.pointer):
            result = f"({result})"
        return f"{result}[{d.count}]"
    if isinstance(d, cpp.function.function):
        result = f"{_generate_declarator(d.get_sub_declarator(), relative_name, table)}"
        if isinstance(d.get_sub_declarator(), cpp.declarator.pointer):
            result = f"({result})"
        
        def generate_param(param: cpp.function.parameter) -> str:
            r = _cat_str(
                'this' if param.this else '',
                _generate_specifier_seq(param.decl_specifier_seq, relative_name, table),
                _generate_declarator(param.declarator, relative_name, table)
            )
            if param.initializer is not None:
                r = _cat_str(r, _generate_initializer(param.initializer, relative_name, table))
            return r
        
        result += f"({', '.join([generate_param(p) for p in d.parameter_list])})"
        result = _cat_str(
            result,
            d.const.name if d.const else '',
            d.volatile.name if d.volatile else '',
            'noexcept' if d.noexcept else ''
        )
        return result
    raise 'fuck you'
