import copy
import typing

import past.language as cpp
import vk.lang.category
import vk.lang.statement as vls

from ..lang.module import macro_module_info, key, module_table, subcomponent

def _find_module(module_struct: list[tuple[cpp.location.source_location, macro_module_info]], target_location: cpp.location.source_location) -> typing.Optional[macro_module_info]:
    for location, info in reversed(module_struct):
        if target_location.file != location.file:
            continue
        if location.position < target_location.position:
            return info
    return None

def classify_module(module_struct: list[tuple[cpp.location.source_location, macro_module_info]], p: dict[cpp.name.name, vls.vk]) -> dict[cpp.name.name, key]:
    result: dict[cpp.name.name, key] = {}
    
    for mangling, vk_stmt in p.items():
        info = _find_module(module_struct, vk_stmt.location)
        assert info is not None
        result[copy.deepcopy(mangling)] = info.key
    
    return result
    

def make_module_table(table: module_table, pps: dict[cpp.name.name, vls.plus_plus]):
    for mangling, vpp in pps.items():
        m = table[vpp.module_key.module]
        assert m is not None
        c = m[vpp.module_key.component]
        assert c is not None
        sc = c[vpp.module_key.subcomponent]
        if sc is None:
            sc = subcomponent(
                name=vpp.module_key.subcomponent,
                symbols=[],
                depends=set(),
            )
            c.subcomponents.append(sc)
        sc.symbols.append(mangling)
        depends = vpp.symbol.get_depend_names()
        for depend_name in depends:
            if depend_name.qualified_name.startswith('::std::'):
                continue
            mk = pps[depend_name].module_key
            if mk == vpp.module_key:
                continue
            sc.depends.add(mk)
        
        
    