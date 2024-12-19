from dataclasses import dataclass

import past.language.symbol

from .category import cpp_symbol as _cpp_symbol

@dataclass
class statement:
    category: _cpp_symbol
    symbol: past.language.symbol.symbol

class _category:
    """
    
    """
    
    handle = 0
    """
    VK_DEFINE_HANDLE(x)

    typedef struct x_T *x;

    cursor:
        struct x_T;
        typedef struct x_T *x;
    
    stmt:
        <class_::x_T, incomplete>
        <typedef> <elaborated::<declared::x_T>> <*<x>>
    
    symbol:
        c:
            <x_T>
                <class_::x_T, incomplete>
                <>
            <x>:
                <elaborated::<declared::x_T>>
                <*>
        cpp:
            <x>:
                <class_::x_T, incomplete>
                <*>
    
    code:
        using <x> = <elaborated::<declared::x_T>> <*>
    """
    
    alias = 1
    """
    cursor:
        typedef ::std::uint_t x
    
    stmt:
        <typedef> <declared::std> <x>
    
    symbol:
        <x>:
            <declared::std>
            <>
    
    code:
        using <x> = <declared::std>
    """
    
    struct = 2
    """
    cursor:
        struct/union x{
            VkStructureType sType;
        };
    
    stmt:
        <class_::x>
    
    symbol:
        <x>:
            <class_::x>
            <>
            
    code:
        struct/union <x>{
        
        }
    """
    
    enum = 3
    """
    cursor:
        enum x{
            y,
            z_company,
        }
    
    stmt:
        <enum::x>
            <y>
            <z><company>
    
    symbol:
        c:
            <x>:
                <enum::x>
                    <y>
                    <z_company>
                <>
        cpp:
            <x>:
                <enum::x>
                    <y>
                <>
            
            <company::x::z>
                <auto>
                <>
                <static_cast>
                    <enum::x>
                    <literal::z>
    
    code
        enum x{
            y,
        }
        
        namespace company::x{
            inline constexpr auto z = static_cast<::x>(z)
        }
    """
    
    function = 4
    """
    cursor:
        return_type x(param_type param_id);
    
    stmt:
        <return_type> <function::<x>>
                            <type::param_type> <param_id>
    
    symbol:
        <x>:
            <return_type>
            <function>
                <param_id>
                    <param_type>
                    <>
                <>
    
    code:
    
    """
    
    using = 5
    """
    cursor:
        typedef x xCompany
    
    stmt:
        <typedef> <declared::x> <x><company>
        
    symbol:
        c:
            <xCompany>
                <declared::x>
                <>
        cpp:
            <company::x>
                <declared::x>
                <>
    
    code:
        namespace company{
            using x;
        }
    """
    
    flag = 6
    """
    cursor:
        typedef VkFlags xFlags
    
    stmt:
        <typedef> <declared::VkFlags> <x><Flags>
        
    symbol:
        <x>:
            <declared::VkFlags>
            <>
    
    code:
        using <x> = VkFlags
    """
    
    flag_bit = 7
    """
    cursor:
        typedef VkFlags64 xFlagBits
    
    stmt:
        <typedef> <declared::VkFlags64> <x><FlagBits>
    
    symbol:
        c:
            <xFlagBits>:
                <declared::VkFlags64>
                <>
        cpp:
            <x>:
                <declared::VkFlags64>
                <>
    
    code:
        using <x> = VkFlags64
        
    cursor:
        enum xFlagBits{ MAX_ENUM = 0x7FFFFFFF, }
        
    stmt:
        <enum::xFlagBits>
            <MAX_ENUM::0x7FFFFFFF>
    
    symbol:
        c:
            <xFlagBits>
                <enum::xFlagBits>
                    <MAX_ENUM::0x7FFFFFFF>
                <>
        cpp:
            <x_bits::>
                <enum::>
                    <_max_enum::0x7FFFFFFF>
                <>
            <x_bits::underlying_type>
                <decltype>
                    <identifier::x_bits::_max_enum>
                <>
    code:
        namespace x_bits{
            enum { _MAX_ENUM = 0x7FFFFFFF, }
            using underlying_type = ::std::underlying_type_t<decltype(x_bits::_MAX_ENUM)>
        }
    """
    
    flag_bit_v = 8
    """
    cursor:
        static const yFlagBits x = z
    stmt:
        <static><const><y><FlagBits> <x> <z>
    symbol:
        c:
            <x>:
                <declared::yFlagBits>
                <>
                <z>
        cpp:
            <y_bits::x>
                <declared::underlying_type>
                <>
                <z>
    code:
        namespace y_bits{
            inline constexpr auto x = z
        }
    """
    flag64 = 9
    flag64_bit = 10
    flag64_bit_v = 11
    pfn = 12
    pfn_decl = 13