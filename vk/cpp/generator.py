import dataclasses
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
import vk.lang.module


def _create_statement_from_vs(vs: vls.plus_plus, table: cpp.symbol.symbol_table) -> cpp.declaration.declaration:
    category = vs.cpp_category
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
        if category in [symbols.flag, symbols.flag64, symbols.flag_bit, symbols.flag64_bit, symbols.alias]:
            spe = symbol.type_id.decl_specifier_seq[0]
            if isinstance(spe, cpp.specifier.declared_type) and not spe.name.qualified_name.startswith('::std::'):
                ref_symbol = table(spe.name)
                if ref_symbol.name.spelling == symbol.name.spelling:
                    return cpp.using_declaration.using(
                        namespace=symbol.name.namespace,
                        identifier=spe.name
                    )
        result = cpp.type_alias.alias(
                                            identifier=symbol.name,
                                            attribute=[],
                                            type_id=symbol.type_id,
                                        )
        return result
        

def environment_header(api: str) -> str:
    result = """#pragma once

#include <cstdint>
#include <cstddef>
#include <type_traits>
#include <concepts>
#include <limits>

#if __has_include(<vulkan/vk_platform.h>)
#	include <vulkan/vk_platform.h>
#endif

#if defined(VKAPI_ATTR)
#\tif !defined(VKAPI_CALL) || !defined(VKAPI_PTR)
#\t\terror "VKAPI_ATTR is defined but VKAPI_CALL or VKAPI_PTR is not defined"
#\tendif
#\tdefine VULKAN_KILLER_ATTRIBUTE VKAPI_ATTR
#\tdefine VULKAN_KILLER_CALL VKAPI_CALL
#\tdefine VULKAN_KILLER_PTR VKAPI_PTR
#elif defined(_WIN32)
#\tdefine VULKAN_KILLER_ATTRIBUTE
#\tdefine VULKAN_KILLER_CALL __stdcall
#\tdefine VULKAN_KILLER_PTR
#elif defined(__ANDROID__) && defined(__ARM_ARCH) && __ARM_ARCH < 7
#\terror "Vulkan is not supported for the 'armeabi' NDK ABI"
#elif defined(__ANDROID__) && defined(__ARM_ARCH) && __ARM_ARCH >= 7 && defined(__ARM_32BIT_STATE)
#\tdefine VULKAN_KILLER_ATTRIBUTE __attribute__((pcs("aapcs-vfp")))
#\tdefine VULKAN_KILLER_CALL
#\tdefine VULKAN_KILLER_PTR VULKAN_KILLER_ATTRIBUTE
#else
#\tdefine VULKAN_KILLER_ATTRIBUTE
#\tdefine VULKAN_KILLER_CALL
#\tdefine VULKAN_KILLER_PTR
#endif

namespace vulkan_killer {
\ttemplate<::std::integral auto MaxEnum, ::std::integral auto MinEnum>
\tstruct _calculate_enum_underlying_type
\t{
\t\tenum
\t\t{
\t\t\tmin_enum = MinEnum,
\t\t\tmax_enum = MaxEnum,
\t\t};
\t\tusing type = ::std::underlying_type_t<decltype(max_enum)>;
\t};
\t
\ttemplate<::std::integral auto MaxEnum, ::std::integral auto MinEnum = 0u>
\tusing _calculate_enum_underlying_type_t = typename _calculate_enum_underlying_type<MaxEnum, MinEnum>::type;
\t
\tstatic_assert(sizeof(::std::uintptr_t) == sizeof(::std::uint64_t));
}

"""
    result = result.replace('VULKAN_KILLER', api.upper())
    result = result.replace('vulkan_killer', api.lower())
    return result

def _extension_guard(api: str, module_key: vk.lang.module.key) -> str:
    result = \
"""#if !defined(VULKAN_KILLER_MODULE_NAME_COMPONENT_NAME)
#\tdefine VULKAN_KILLER_MODULE_NAME_COMPONENT_NAME 1
#endif
"""
    result = result.replace('VULKAN_KILLER', api.upper())
    result = result.replace('MODULE_NAME', module_key.module.upper())
    result = result.replace('COMPONENT_NAME', module_key.component.upper())
    return result
    

@dataclasses.dataclass
class generated_result:
    file: str
    code: str
    
    def __hash__(self):
        return (self.file, self.code).__hash__()

relative_name_t = typing.Callable[[cpp.name.name], str]

@dataclasses.dataclass
class _generator_context:
    api: str
    relative_name: relative_name_t
    table: past.language.symbol.symbol_table

def generate(api: str, vkpp_module_struct: list[vk.lang.module.key], vkpp_module_table: vk.lang.module.module_table, vkpp_symbol_table: dict[cpp.name.name, vls.plus_plus]) -> set[generated_result]:
    root = node('')
    
    result: set[generated_result] = set[generated_result]()
    
    environment_h = generated_result(
        file=f"{api}/core/environment.h",
        code=environment_header(api),
    )
    result.add(environment_h)
    
    def get_symbol_by_mangling(m: cpp.name.name) -> cpp.symbol.symbol:
        return vkpp_symbol_table[m].symbol
    
    generated_keys = set[vk.lang.module.key]()
    
    for module_key in vkpp_module_struct:
        if module_key in generated_keys:
            continue
        module = vkpp_module_table[module_key.module]
        component = module[module_key.component]
        
        component.other_depends = component.other_depends or set()
        component.other_depends.add(environment_h.file)
        coder = _code()
        
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
        
        context = _generator_context(
            api=api,
            relative_name=relative_name,
            table=get_symbol_by_mangling,
        )
        
        coder.write_line(f"#pragma once")
        coder.write_line()
        
        for depend_header in component.other_depends:
            coder.write_line(f"#include <{depend_header}>")
        for depend_header in component.depends:
            coder.write_line(f"#include <{api}/{depend_header.module}/{depend_header.component}.h>")
        coder.write_line()
        
        coder.write_line(_extension_guard(api, vk.lang.module.key(
            module=module.name,
            component=component.name,
        )))
        
        for vkpp_symbol_mangling in component.symbols:
            vs = vkpp_symbol_table[vkpp_symbol_mangling]
            category: vlc.cpp_symbol = vs.cpp_category
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
                v = int(symbol.initializer.expression.evaluate())
                from .mangle import _is_int32_max, _std_int32_max
                
                coder.write_line(
                    f"using underlying_type = _calculate_enum_underlying_type_t<{_std_int32_max() if _is_int32_max(v) else hex(v).lower()}>;")
                continue
            
            coder.write_line(
                _generate_statement(_create_statement_from_vs(vs, get_symbol_by_mangling), context))
        
        coder.change_namespace([''])
        
        result.add(generated_result(
            file=f"{api}/{module.name}/{component.name}.h",
            code=coder.data
        ))
        generated_keys.add(module_key)
    
    return result

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


def _generate_type(t: cpp.type.type_id, context: _generator_context) -> str:
    if isinstance(t, cpp.type.type_id):
        return _cat_str(
            _generate_specifier_seq(t.decl_specifier_seq, context),
            _generate_declarator(t.declarator, context),
        )
    raise 'fuck you'


def _generate_statement(s: cpp.statement.statement, context: _generator_context) -> str:
    if isinstance(s, cpp.declaration.declaration):
        if isinstance(s, cpp.declaration.block):
            if isinstance(s, cpp.declaration.simple):
                return _cat_str(
                    _generate_specifier_seq(s.decl_specifier_seq, context),
                    _generate_init_declarator_seq(s.init_declarator_seq, context),
                ) + ';'
            if isinstance(s, cpp.type_alias.alias):
                return _cat_str(
                    'using',
                    s.identifier.spelling,
                    '=',
                    _generate_type(s.type_id, context),
                ) + ';'
            if isinstance(s, cpp.using_declaration.using):
                return _cat_str(
                    'using',
                    # relative_name(table[s.identifier].name)
                    context.table(s.identifier).name.qualified_name
                ) + ';'
    raise 'fuck you'


def _generate_specifier_seq(ss: list[cpp.specifier.specifier], context: _generator_context) -> str:
    return ' '.join([_generate_specifier(s, context) for s in ss])


def _generate_specifier(s: cpp.specifier.specifier, context: _generator_context) -> str:
    if isinstance(s, cpp.keyword.keyword) and not isinstance(s, cpp.specifier.decltype):
        return s.name
    if isinstance(s, cpp.specifier.typed):
        if isinstance(s, cpp.specifier.fundamental):
            return s.type if isinstance(s.type, str) else s.type.name
        if isinstance(s, cpp.specifier.decltype):
            result = f"{s.name}"
            d = context.table(s.entry)
            assert d is not None
            result += f"({context.relative_name(d.name)})"
            return result
        if isinstance(s, cpp.specifier.declared_type):
            if len(s.name.namespace) == 2 and s.name.namespace[0] == '' and s.name.namespace[1] == 'std':
                return s.name.qualified_name
            d = context.table(s.name)
            assert d is not None
            return f"{context.relative_name(d.name)}"
        if isinstance(s, cpp.specifier.elaborated_type):
            return _cat_str(s.key.name, _generate_specifier(s.identifier, context))
        if isinstance(s, cpp.class_.class_):
            result = _cat_str(s.class_key.name, s.head_name.spelling)
            if s.members is not None:
                result += '\n{\n' if len(s.members) else '{'
                for member in s.members:
                    result += f'\t{_generate_specifier_seq(member.decl_specifier_seq, context)}'
                    if len(member.member_declarator_seq):
                        result += ' '
                    
                    def generate_member_ds(ds: cpp.init_declarator.init_declarator | cpp.bit_field.bit_field) -> str:
                        if isinstance(ds, cpp.init_declarator.init_declarator):
                            return _generate_init_declarator(ds, context)
                        return _cat_str(ds.identifier, ':', ds.width,
                                        '' if not ds.initializer else _generate_initializer(ds.initializer,
                                                                                            context))
                    
                    result += ', '.join(generate_member_ds(d) for d in member.member_declarator_seq)
                    result += ';\n'
                result += '}'
            return result
        if isinstance(s, cpp.enum.enum_specifier):
            result = _cat_str(s.key.name, s.head_name.spelling)
            if s.base is not None:
                assert isinstance(s.base, tuple)
                from .mangle import _is_int32_max, _std_int32_max
                max, min = int(s.base[0]), int(s.base[1])
                result = _cat_str(result, ':', f"_calculate_enum_underlying_type_t<{_std_int32_max() if _is_int32_max(max) else hex(max).lower()}, {_std_int32_max() if _is_int32_max(min) else hex(min).lower()}>")
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


def _generate_init_declarator(d: cpp.init_declarator.init_declarator, context: _generator_context) -> str:
    return _cat_str(
        _generate_declarator(d.declarator, context),
        _generate_initializer(d.initializer, context) if d.initializer is not None else ''
    )


def _generate_init_declarator_seq(d: list[cpp.init_declarator.init_declarator], context: _generator_context) -> str:
    return ', '.join([_generate_init_declarator(dd, context) for dd in d])


def _generate_expression(e: cpp.expression.expression, context: _generator_context) -> str:
    if isinstance(e, cpp.expression.primary):
        if isinstance(e, cpp.expression.literal):
            return str(e.value)
        if isinstance(e, cpp.expression.identifier):
            symbol = context.table(e.entry)
            assert isinstance(symbol, cpp.declarator.declarator)
            return context.relative_name(symbol.introduced_name())
        raise 'fuck you'
    if isinstance(e, cpp.expression.conversion):
        if isinstance(e, cpp.expression.static_cast):
            return f"static_cast<{_generate_type(e.cast_to, context)}>({_generate_expression(e.subexpression, context)})"
        
    raise 'fuck you'


def _generate_initializer(i: cpp.initialization.initializer, context: _generator_context) -> str:
    if isinstance(i, cpp.initialization.copy):
        return _cat_str(
            '=',
            _generate_expression(i.expression, context)
        )
    raise 'fuck you'


def _generate_declarator(d: cpp.declarator.declarator, context: _generator_context) -> str:
    if isinstance(d, cpp.declarator.abstract):
        return ''
    if isinstance(d, cpp.declarator.name):
        return d.identifier.spelling  # relative_name(d.identifier)
    if isinstance(d, cpp.declarator.pointer):
        return '*' + _cat_str(
            d.const.name if d.const else '',
            d.volatile.name if d.volatile else '',
            _generate_declarator(d.get_sub_declarator(), context)
        )
    if isinstance(d, cpp.declarator.array):
        result = f"{_generate_declarator(d.get_sub_declarator(), context)}"
        if isinstance(d.get_sub_declarator(), cpp.declarator.pointer):
            result = f"({result})"
        return f"{result}[{d.count}]"
    if isinstance(d, cpp.function.declarator):
        result = f"{context.api.upper()}_CALL {_generate_declarator(d.get_sub_declarator(), context)}"
        if isinstance(d.get_sub_declarator(), cpp.declarator.pointer):
            result = f"({result})"
        
        def generate_param(param: cpp.function.parameter) -> str:
            r = _cat_str(
                'this' if param.this else '',
                _generate_specifier_seq(param.decl_specifier_seq, context),
                _generate_declarator(param.declarator, context)
            )
            if param.initializer is not None:
                r = _cat_str(r, _generate_initializer(param.initializer, context))
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
