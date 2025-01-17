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


def structure_type(program: dict[cpp.name.name, vls.plus_plus]):
    
    for mangling, vs in program.items():
        if vs.cpp_category != symbols.struct:
            continue
        symbol = vs.symbol
        spe: cpp.class_.class_ = cpp.specifier_seq.get_one_specifier_by_type(symbol.type_id.decl_specifier_seq,
                                                                             cpp.class_.class_)
        assert spe is not None
        if spe.members is None or not len(spe.members):
            continue
        first = spe.members[0]
        m_spe = cpp.specifier_seq.get_one_specifier_by_type(first.decl_specifier_seq, cpp.specifier.declared_type)
        if m_spe is None:
            continue
        if m_spe.name.qualified_name != '::VkStructureType':
            continue
        struct_name = symbol.mangling.spelling
        struct_name_id = identifier(struct_name)
        struct_type_name = f"VK_STRUCTURE_TYPE_{'_'.join([word.upper() for word in struct_name_id.id])}"
        if struct_name_id.company:
            struct_type_name += f"_{struct_name_id.company.upper()}"
        if struct_name_id.ext:
            struct_type_name += '_EXT'
        struct_type_mangling = cpp.name.name(
            namespace=[''],
            spelling=struct_type_name,
        )
        if struct_type_mangling not in program.keys():
            logging.warn(f"{struct_name} is not vulkan structure")
            continue
        
        assert len(first.member_declarator_seq) == 1
        init_decl = first.member_declarator_seq[0]
        assert isinstance(init_decl, cpp.init_declarator.init_declarator)
        assert init_decl.initializer is None
        
        # first.decl_specifier_seq.append(cpp.cv.const())
        init_decl.initializer = cpp.initialization.copy(
            expression=cpp.expression.identifier(
                entry=struct_type_mangling
            )
        )
