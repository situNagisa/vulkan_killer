import copy

import past.language as cpp
import past.language.symbol
import past.language.declaration
import past.language.type_alias
import past.language.init_declarator

import vk.lang.statement as vls
from vk.lang.category import mangling as category_mangling
from vk.lang.category import cpp_symbol as symbols
from vk.lang.name import identifier

import logging

def _is_fundamental_type(s: cpp.symbol.symbol, table: cpp.symbol.symbol_table) -> bool:
    if isinstance(s.type_id.declarator, cpp.declarator.compound):
        return False
    spe: cpp.specifier.declared_type = cpp.specifier_seq.get_one_specifier_by_type(s.type_id.decl_specifier_seq, cpp.specifier.declared_type)
    if spe is None:
        spe: cpp.specifier.elaborated_type = cpp.specifier_seq.get_one_specifier_by_type(s.type_id.decl_specifier_seq, cpp.specifier.elaborated_type)
        if spe is None:
            return isinstance(cpp.specifier_seq.typed_only(s.type_id.decl_specifier_seq)[0], cpp.specifier.fundamental)
        name: cpp.name.name = spe.identifier.name
    else:
        name: cpp.name.name = spe.name
    if name.qualified_name.startswith('::std::'):
        return True
    return _is_fundamental_type(table(name), table)

def vulkan_c_type(api: str, program: dict[cpp.name.name, vls.plus_plus]):
    def get_symbol_by_mangling(m: cpp.name.name) -> cpp.symbol.symbol:
        return program[m].symbol
    
    ready: dict[cpp.name.name, vls.plus_plus] = {}
    for mangling, vs in program.items():
        symbol = vs.symbol
        if symbol.category != cpp.symbol.category.type:
            continue
        if vs.cpp_category in [symbols.pfn, symbols.pfn_decl]:
            continue
        if _is_fundamental_type(symbol, get_symbol_by_mangling):
            continue
        new_mangling = copy.deepcopy(mangling)
        new_mangling.spelling += '_vulkan_c_type'
        new_vls_name = cpp.name.name(
                            namespace=['', api],
                            spelling='vulkan_c_type',
                        )
        new_vls = vls.plus_plus(
            module_key=copy.deepcopy(vs.module_key),
            mangling_category=category_mangling.none,
            cpp_category=symbols.vulkan_c_api,
            symbol=cpp.symbol.symbol(
                type_id=cpp.type.type_id(
                    decl_specifier_seq=[cpp.class_.class_(
                        attribute=[],
                        class_key=cpp.keyword.class_.struct,
                        head_name=new_vls_name,
                        members=None,
                        bases=[cpp.class_.base_clause(
                            attribute=[],
                            virtual=False,
                            access_specifier=None,
                            class_or_computed=cpp.specifier.declared_type(
                                name=mangling
                            )
                        )],
                    )]
                ),
                category=cpp.symbol.category.type,
                mangling=new_mangling,
                initializer=None,
                name=new_vls_name,
            )
        )
        new_vls.module_key.subcomponent = 'vulkan_c_type'
        ready[new_mangling] = new_vls
    
    program.update(ready)
