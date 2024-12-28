import copy
from dataclasses import dataclass

from .keyword import keyword, keyword_enum
from .name import depender, name
'''
specifier
    keyword_specifier
        typedef
        inline
        friend
    keyword
        function
        compile_time
        storage_class
    typed
        simple
            class
            fundamental
            auto
            decltype
            declared_type
        elaborated
        typename
'''


class specifier:
    pass


class _keyword_specifier(keyword):
    
    @property
    def name(self) -> str:
        return type(self).__name__.removeprefix('_')


class typedef(specifier, _keyword_specifier):
    pass


class function(specifier, keyword_enum):
    inline = 0
    virtual = 1
    explicit = 2


class inline(specifier, _keyword_specifier):
    pass


class friend(specifier, _keyword_specifier):
    pass


@dataclass
class compile_time(specifier, keyword_enum):
    constexpr = 0
    consteval = 1
    constinit = 2


@dataclass
class storage_class(specifier, keyword_enum):
    register = 0
    static = 1
    thread_local = 2
    extern = 3
    extern_c = 'extern \"C\"'
    mutable = 4


class typed(specifier):
    pass


class simple_type(typed):
    pass


@dataclass
class fundamental(simple_type):
    from .keyword import type as _type
    type: _type | str


@dataclass
class auto(simple_type, _keyword_specifier):
    pass


@dataclass
class decltype(simple_type, _keyword_specifier, depender):
    from .name import name as _name
    entry: _name
    
    def __init__(self, entry: _name):
        self.entry = copy.deepcopy(entry)
        
    def get_depend_names(self) -> set[name]:
        return {self.entry}


@dataclass
class declared_type(simple_type, depender):
    from .name import name as _name
    name: _name
    
    def __init__(self, name: _name):
        self.name = copy.deepcopy(name)
        
    def get_depend_names(self) -> set[name]:
        return {self.name}


@dataclass
class elaborated_type(typed, depender):
    from .keyword import class_ as _class
    from .keyword import enum as _enum
    
    key: _class | _enum
    identifier: declared_type
    
    def get_depend_names(self) -> set[name]:
        return self.identifier.get_depend_names()


@dataclass
class typename(typed, _keyword_specifier):
    pass
