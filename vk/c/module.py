import dataclasses
import logging
import typing

import clang.cindex as cci
import past.language as cpp
from ..lang.module import macro_module_info, module_table, module, component, key, subcomponent
from ..lang.name import generate_module_key, core_module, extension_module, extension_category
from ..lang.name import module as module_trait

def module_struct(file: str) -> tuple[module_table, list[tuple[cpp.location.source_location, macro_module_info]]]:
    index = cci.Index.create(excludeDecls=True)
    tu = index.parse(file,
                     options=cci.TranslationUnit.PARSE_DETAILED_PROCESSING_RECORD,
                     # args=['-DVKAPI_PTR=__stdcall']
                     )
    translate_unit: cci.Cursor = tu.cursor
    
    children: list[cci.Cursor] = list(translate_unit.get_children())
    infos: list[tuple[cpp.location.source_location, macro_module_info]] = []
    table: module_table = module_table()
    
    defined_macro: dict[str, int] = {}
    current_module: typing.Optional[tuple[key, cpp.location.source_location]] = None
    for child in children:
        if child.kind != cci.CursorKind.MACRO_DEFINITION:
            continue
        spelling: str = child.spelling
        trait = module_trait(spelling)
        if trait.info is None:
            continue
        if trait.api != 'VK':
            continue
        info: macro_module_info = macro_module_info(
            key=generate_module_key(trait),
            version=0,
        )
        assert info.key is not None
        if isinstance(trait.info, core_module):
            info.version = (trait.info.major, trait.info.minor)
            location: cci.SourceLocation = child.location
            assert location.file is not None
            infos.append((cpp.location.source_location(
                file=cpp.location.file(location.file.name),
                position=cpp.location.position(
                    line=location.line,
                    column=location.column,
                )
            ), info))
        elif isinstance(trait.info, extension_module):
            match trait.info.category:
                case extension_category.guard:
                    location: cci.SourceLocation = child.location
                    assert location.file is not None
                    current_module = (info.key, cpp.location.source_location(
                        file=cpp.location.file(location.file.name),
                        position=cpp.location.position(
                            line=location.line,
                            column=location.column,
                        )
                    ))
                    continue
                case extension_category.extension_name:
                    continue
                case extension_category.spec_version:
                    tokens: list[str] = [token.spelling for token in child.get_tokens()]
                    version_token = tokens[1]
                    if version_token.isdigit():
                        info.version = int(version_token)
                    else:
                        assert version_token in defined_macro
                        info.version = defined_macro[version_token]
                    cur_key, cur_loc = current_module
                    if cur_key != info.key:
                        logging.warn(f"cur key {cur_key} not equal info key {info.key}")
                    infos.append((cur_loc, info))
        else:
            raise 'fuck you'
        
        defined_macro[spelling] = info.version
        
        m = table[info.key.module]
        if m is None:
            m = module(
                name=info.key.module,
                components=[]
            )
            table.modules.append(m)
        assert info.key.component not in m
        c = component(
            name=info.key.component,
            version=info.version if isinstance(info.version, int) else None,
            subcomponents=[],
        )
        m.components.append(c)
        
    
    return table, infos