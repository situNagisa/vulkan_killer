import enum

import past.language as cpp


class stmt(enum.Enum):
    none = 0
    typedef = 1
    """
    typedef <specifier-seq> <identifier>
    """
    
    class_ = 2
    """
    struct <identifier>;
    struct <identifier> { };
    union <identifier> { };
    """
    
    enum = 3
    """
    enum <identifier> { };
    """
    
    function = 4
    """
    <type-specifier> <identifier>(<param-list>)
    """
    
    variable = 5
    """
    static const <declared-specifier> <identifier> = <copy-initializer>
    """
    
    def is_type(self) -> bool:
        return self in [stmt.typedef, stmt.class_, stmt.enum]
    
    def is_value(self) -> bool:
        return self in [stmt.function, stmt.variable, stmt.enum]
    
    @staticmethod
    def symbol_be_declared_on(s: cpp.symbol.symbol):
        spe_seq = cpp.specifier_seq.typed_only(s.type_id.decl_specifier_seq)
        if s.category == cpp.symbol.category.type:
            assert s.initializer is None
            if len(spe_seq) == 1:
                spe = spe_seq[0]
                if isinstance(spe, cpp.name.name_introducer) and spe.introduced_name() == s.name:
                    if isinstance(spe, cpp.class_.class_):
                        return stmt.class_
                    if isinstance(spe, cpp.enum.enum_specifier):
                        return stmt.enum
            return stmt.typedef
        if s.category == cpp.symbol.category.value:
            if isinstance(s.type_id.declarator, cpp.function.declarator):
                return stmt.function
            if len(spe_seq) == 1 and isinstance(spe_seq[0], cpp.specifier.declared_type):
                return stmt.enum
            if isinstance(s.type_id.declarator, cpp.declarator.abstract):
                return stmt.variable
        return stmt.none


class c_symbol(enum.Enum):
    none = 0
    function = 100
    """
    <value> <type> <function> <none>
    """
    flag_bit_v = 101
    """
    <flag><bit>
    <value> <declared> <abstract> <copy>
    """
    flag64_bit_v = 102
    """
    <flag><bit><two>
    <value> <declared> <abstract> <copy>
    """
    
    handle_struct = 200
    """
    <handle_struct>
    <type> <incomplete-class> <abstract>
    """
    handle = 201
    """
    <type> <elaborated<declared>> <pointer>
    """
    alias = 202
    """
    <type> <declared-std> <abstract>
    """
    struct = 203
    """
    <type> <class-complete> <abstract>
    """
    enum = 204
    """
    <type> <enum-complete> <abstract>
    """
    using = 205
    """
    <company><ext>
    <type> <declared> <abstract>
    """
    flag = 206
    """
    <flag>
    <type> VkFlags <abstract>
    """
    flag_bit = 207
    """
    <flag><bit>
    <type> VkFlags64 <abstract>
    """
    enum_bit = 208
    """
    <flag><bit>
    <type> <enum> <abstract>
    """
    flag64 = 209
    """
    <flag><two>
    <type> VkFlags64 <abstract>
    """
    flag64_bit = 210
    """
    <flag><two><bit>
    <type> VkFlags64 <abstract>
    """
    pfn = 211
    """
    <pfn>
    <type> <type> <function<pointer>>
    """
    enumerator = 212
    
    @staticmethod
    def create(c: stmt, s: cpp.symbol.symbol):
        from .name import identifier, enumerator
        if s.category == cpp.symbol.category.value:
            if c == stmt.function:
                assert s.initializer is None
                return c_symbol.function
            if c == stmt.variable:
                spe: cpp.specifier.declared_type = cpp.specifier_seq.get_one_specifier_by_type(s.type_id.decl_specifier_seq, cpp.specifier.declared_type)
                assert spe is not None
                e_trait = identifier(spe.name.spelling)
                assert e_trait.flag and e_trait.bit
                trait = enumerator(spe.name.spelling, s.mangling.spelling)
                assert e_trait.two == trait.two
                assert isinstance(s.initializer, cpp.initialization.copy)
                if trait.two:
                    return c_symbol.flag64_bit_v
                return c_symbol.flag_bit_v
            if c == stmt.enum:
                spe: cpp.specifier.declared_type = cpp.specifier_seq.get_one_specifier_by_type(s.type_id.decl_specifier_seq, cpp.specifier.declared_type)
                assert spe is not None
                e_trait = identifier(spe.name.spelling)
                if not e_trait.flag:
                    return c_symbol.enumerator
                assert e_trait.bit
                trait = enumerator(spe.name.spelling, s.mangling.spelling)
                assert e_trait.two == trait.two
                if trait.two:
                    return c_symbol.flag64_bit_v
                return c_symbol.flag_bit_v
            
            return c_symbol.none
        
        if s.category == cpp.symbol.category.type:
            assert s.initializer is None
            spes = [spe for spe in s.type_id.decl_specifier_seq if isinstance(spe, cpp.specifier.typed) and not isinstance(spe, cpp.cv.const) and not isinstance(spe, cpp.cv.volatile)]
            assert len(spes) == 1
            spe = spes[0]
            trait = identifier(s.mangling.spelling)
            
            if c == stmt.typedef:
                if trait.pfn:
                    # assert isinstance(s.type_id.declarator, cpp.function.function)
                    # assert isinstance(s.type_id.declarator.get_sub_declarator(), cpp.declarator.pointer)
                    return c_symbol.pfn
                
                if isinstance(spe, cpp.specifier.declared_type):
                    assert isinstance(s.type_id.declarator, cpp.declarator.abstract)
                    if len(spe.name.namespace) >= 2 and spe.name.namespace[0] == '' and spe.name.namespace[1] == 'std':
                        return c_symbol.alias
                    if spe.name.qualified_name == '::VkFlags':
                        assert trait.flag and not trait.bit and not trait.two
                        return c_symbol.flag
                    if spe.name.qualified_name == '::VkFlags64':
                        assert trait.flag
                        if trait.two:
                            return c_symbol.flag64_bit if trait.bit else c_symbol.flag64
                        # assert trait.bit
                        return c_symbol.flag_bit if trait.bit else c_symbol.flag
                    if trait.flag:
                        if trait.bit:
                            return c_symbol.flag64_bit if trait.two else c_symbol.flag_bit
                        return c_symbol.flag64 if trait.two else c_symbol.flag
                    # spe_trait = identifier(spe.name.spelling)
                    # if spe_trait.id == trait.id:
                    #     assert spe_trait.company != trait.company or spe_trait.ext != trait.ext
                    #     return c_symbol.using
                elif isinstance(spe, cpp.specifier.elaborated_type):
                    spe_trait = identifier(spe.identifier.name.spelling)
                    assert isinstance(s.type_id.declarator, cpp.declarator.pointer)
                    assert spe_trait.handle_struct
                    return c_symbol.handle
                
                print(f"cnm sb vulkan: typedef {spe} {s.name.spelling}")
                return c_symbol.alias
            
            if c == stmt.class_:
                assert isinstance(spe, cpp.class_.class_)
                if spe.members is None:
                    assert trait.handle_struct
                    return c_symbol.handle_struct
                assert not trait.handle_struct
                return c_symbol.struct
            
            if c == stmt.enum:
                assert isinstance(spe, cpp.enum.enum_specifier)
                assert spe.enumerator_list is not None
                if trait.flag:
                    assert trait.bit
                    return c_symbol.enum_bit
                return c_symbol.enum
            
            return c_symbol.none
        
        return c_symbol.none


class cpp_symbol(enum.Enum):
    none = 0
    function = 100
    """
    c::<id>
    """
    flag_bit_v = 101
    """
    <enum>_bits::<id>
    """
    flag64_bit_v = 102
    """
    <enum>_bits::<id>
    """
    enumerator = 103
    """
    <enum>::<id>
    """
    inner_enumerator = 104
    
    max_enum = 105
    """
    <enum>_bits::underlying_type
    """
    
    def is_enumerator(self) -> bool:
        return cpp_symbol.flag_bit_v.value <= self.value <= cpp_symbol.inner_enumerator.value
    
    def is_value(self) -> bool:
        return cpp_symbol.function.value <= self.value <= cpp_symbol.max_enum.value
    
    handle = 201
    """
    <id>_handle
    """
    alias = 210
    """
    
    """
    
    struct = 220
    
    enum = 230
    
    using = 240
    
    flag = 241
    flag_bit = 242
    flag64 = 243
    flag64_bit = 244
    
    pfn = 250
    pfn_decl = 251
    
    vulkan_c_api = 300
    

    def is_type(self) -> bool:
        return cpp_symbol.handle.value <= self.value <= cpp_symbol.pfn_decl.value
                
    
class mangling(enum.Enum):
    none = 0,
    
    # function
    function = 110,
    """
    vk<id> -> c::vk<id>
    """
    function_ptr_decl = 111,
    """
    PFN_<id> -> c::<id>
    """
    function_ptr = 112,
    
    # enum
    enum = 120,
    enumerator = 121,
    """
    VK_[enum]_<id> -> <enum>::<id>
    """
    enumerator_none = 122,
    """
    VK_<enum>_NONE -> <enum>::none
    """
    
    # flag
    flag = 130,
    """
    Vk<id>Flags -> <id>_flag
    """
    flag64 = 131,
    """
    Vk<id>Flags2 -> <id>_flag64
    """
    flag_bit = 132,
    """
    Vk<id>FlagBits -> <id>_bits::underlying_type
    """
    flag64_bit = 133,
    """
    Vk<id>FlagBits2 -> <id>64_bits::underlying_type
    """
    flag_bit_v = 134,
    """
    VK_<enum>_<id> -> <enum>_bits::<id>_
    """
    flag_bit_bit_v = 135,
    """
    VK_<enum>_<id>_BIT -> <enum>_bits::<id>
    """
    flag_bit_none_v = 136,
    """
    VK_<enum>_NONE -> <enum>_bits::none
    """
    
    # alias
    alias = 140,
    
    # struct
    struct = 150,
    
    # handle
    handle = 160,
    """
    Vk<id> -> handle::<id>
    """
    
    # using
    using = 170,
    using_flag_bit = 171,
    using_flag64_bit = 172,
    
    def is_enumerator(self) -> bool:
        return self in [
            mangling.enumerator, mangling.enumerator_none,
            mangling.flag_bit_v, mangling.flag_bit_bit_v, mangling.flag_bit_none_v
        ]
    
    def is_using(self) -> bool:
        return self in [
            mangling.using, mangling.using_flag_bit, mangling.using_flag64_bit
        ]