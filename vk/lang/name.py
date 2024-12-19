'''
这个文件用于描述vulkan的命名规则

在开始之前, 让我先吐槽一下
首先, vulkan的命名就是一坨屎, khr之前造了opengl那坨屎还觉得不够, 还有再造一坨
opengl是完全的屎, 从命名到设计, 能tm想出用状态机也真是tmd人才
vulkan的命名是彻底的屎
什么tmd名称与类型信息耦合
什么tmd自己不遵循自己的规则
什么tmd乱占用前缀后缀
这么会造屎早点去死吧, 祸害业界的傻逼

id = 名称
company = 提供这个api对应的公司
ext = 'ext'(忽略大小写)
suffix = [company][ext]

filed_set = Vk<id>[suffix]                                          ->  [snake::suffix]::<snake::id>
handle = Vk<id>[suffix]                                             ->  [snake::suffix]::<snake::id>_handle
handle_struct = <handle>_T                                          ->  [snake::suffix]::_<snake::id>
typedef = Vk<id>[suffix]                                            ->  [snake::suffix]::<snake::id>_t
using = Vk<id>[suffix]                                              ->
function = vk<id>[suffix]                                           ->  [snake::suffix]::c::<function>
pfn = PFN_<function>                                                ->  [snake::suffix]::c::<snake::id>_t
enum = Vk<id>[suffix]                                               ->  [snake::suffix]::<snake::id>
    VK_<enum::id>_<id>                                              ->       <id>
    VK_<enum::id>_<id>_<snake::upper::suffix>                       ->       <snake::suffix>::<snake::id>::<id>
    VK_<enum::id>_<id>_MAX_ENUM                                     ->       max_enum
flag = Vk<id>Flags[suffix]                                          ->  [snake::suffix]::<snake::id>
enum_bit = Vk<id>FlagBits[suffix]                                   ->  [snake::suffix]::<snake::id>_bits::
    VK_<enum::id>_<id>_BIT                                          ->       <id>
    VK_<enum::id>_<id>_BIT_<snake::upper::suffix>                   ->       <snake::suffix>::<snake::id>_bits::<id>
    VK_<enum::id>_FLAG_BITS_MAX_ENUM                                ->       max_enum
flag_64 = Vk<id>Flags2[suffix]                                      ->  [snake::suffix]::<snake::id>_ex
flag_64_bit = Vk<id>FlagBits2[suffix]                               ->  [snake::suffix]::<snake::id>_bits::
    VK_<flag_64::id>_2_<id>_NONE                                    ->      none
    VK_<flag_64::id>_2_<id>_NONE_<suffix>                           ->      <snake::suffix>::<snake::id>_bits::none
    VK_<flag_64::id>_2_<id>_BIT                                     ->      <id>
    VK_<flag_64::id>_2_<id>_BIT_<suffix>                            ->      <snake::suffix>::<snake::id>_bits::<id>

filed =
    <VkStructureType?sType>

可以看到, 无意义的前缀后缀一大堆, tmd去死吧
'''
import dataclasses
import logging

from vk.spliter import split_identifier

companies = [
    'ext', 'khr', 'huawei', 'nv', 'arm', 'qcom', 'amd', 'valve', 'nvx', 'android', 'fuchsia', 'qnx',
    'fuchsia', 'intel', 'lunarg', 'msft'
]


def is_company(name: str) -> bool:
    result = name.lower() in companies
    if result:
        assert name.isupper()
    return result


def is_extension(name: str) -> bool:
    return name.lower() == 'ext'


def _process_suffix(words: list[str]) -> tuple[str, bool]:
    assert len(words)
    ext: bool = is_extension(words[-1])
    if ext:
        words.pop()
    company: str = ''
    if not len(words):
        return company, ext
    if is_company(words[-1]):
        company = words[-1]
        words.pop()
        return company, ext
    for c in companies:
        if not words[-1].lower().endswith(c):
            continue
        assert company == ''
        assert len(words[-1]) > len(c)
        assert words[-1][-(len(c) + 1)].isupper()
        company = c
    if company:
        words[-1] = words[-1][:-len(company)]
    return company, ext


@dataclasses.dataclass(init=False)
class identifier:
    pfn: bool = False
    api: str = ''
    id: list[str] = None
    flag: bool = False
    bit: bool = False
    two: bool = False
    company: str = ''
    ext: bool = False
    handle_struct: bool = False
    
    def __init__(self, sb_name: str):
        words = split_identifier(sb_name)
        
        # pfn
        if not len(words):
            raise 'fuck you'
        if words[0] == 'PFN':
            assert sb_name.startswith('PFN_')
            words = words[1:]
            self.pfn = True
        
        # api
        if len(words) < 2:
            raise 'fuck you'
        if words[0].lower() != 'vk':
            logging.warning(f"不是哥们??, {words[0]}")
        self.api = words[0]
        words = words[1:]
        
        # handle_struct
        if not len(words):
            raise 'fuck you'
        if words[-1] == 'T':
            assert sb_name.endswith('_T')
            words.pop()
            self.handle_struct = True
        
        # suffix
        self.company, self.ext = _process_suffix(words)
        
        # flagbit
        if len(words) > 1 and words[-1] in ['Flags', 'Flags2', 'Bits', 'Bits2']:
            self.flag = True
            if words[-1] == 'Flags':
                words = words[:-1]
            elif words[-1] == 'Flags2':
                self.two = True
                words = words[:-1]
            elif words[-1] == 'Bits':
                assert words[-2] == 'Flag'
                self.bit = True
                words = words[:-2]
            elif words[-1] == 'Bits2':
                assert words[-2] == 'Flag'
                self.bit = True
                self.two = True
                words = words[:-2]
            else:
                raise 'cnm sb vulkan'
        
        self.id = words
        if not len(self.id):
            raise 'fuck you'
    
    def is_vulkan_api(self) -> bool:
        return self.api.lower() == 'vk'


@dataclasses.dataclass(init=False)
class enumerator:
    api: str = ''
    id: list[str] = None
    bit: bool = False
    none: bool = False
    two: bool = False
    company: str = ''
    ext: bool = False
    max_enum: bool = False
    
    def __init__(self, enum_name: str, sb_name: str):
        enum_trait = identifier(enum_name)
        words = split_identifier(sb_name)
        
        # api
        assert len(words) > 1
        if words[0] != 'VK':
            logging.warning(f"不是哥们??, {words[0]}")
        self.api = words[0].lower()
        words = words[1:]
        
        if len(words) >= len(enum_trait.id) and ''.join(words[:len(enum_trait.id)]).lower() == ''.join(enum_trait.id).lower():
            words = words[len(enum_trait.id):]
        
        assert len(words)
        if words[0] == '2':
            self.two = True
            words = words[1:]
        
        # suffix
        self.company, self.ext = _process_suffix(words)
        
        # bit
        assert len(words)
        if words[-1] in ['BIT', 'NONE']:
            self.bit = words[-1] == 'BIT'
            self.none = words[-1] == 'NONE'
            words.pop()
        
        # max enum
        if len(words) > 1 and words[-2] == 'MAX' and words[-1] == 'ENUM':
            self.max_enum = True
            words = words[:-2]
            assert not self.bit
        
        # enum VkSampleCountFlagBits
        if not len(words) and not self.none and self.two:
            self.two = False
            words = ['2']
        
        self.id = words
        assert len(self.id) or self.none or self.max_enum
        
        if enum_trait.company:
            if not self.company:
                self.company = enum_trait.company
                
        
        
        
        
