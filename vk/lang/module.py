import copy
import dataclasses
import typing

import data_struct.tree

import past.language as cpp


@dataclasses.dataclass
class key:
    module: str
    component: str
    subcomponent: str
    
    def __eq__(self, other) -> bool:
        return self.module == other.module and self.component == other.component and self.subcomponent == other.subcomponent
    
    def __deepcopy__(self, memo={}):
        return key(
            module=copy.deepcopy(self.module, memo),
            component=copy.deepcopy(self.component, memo),
            subcomponent=copy.deepcopy(self.subcomponent, memo)
        )
    
    def __hash__(self):
        return (self.module, self.component, self.subcomponent).__hash__()

@dataclasses.dataclass
class subcomponent:
    name: str
    symbols: list[cpp.name.name]
    depends: set[key]
    other_depends: typing.Optional[set[str]] = None

@dataclasses.dataclass
class component(data_struct.tree.tree):
    name: str
    version: typing.Optional[int]
    subcomponents: list[subcomponent]
    
    def children(self) -> list[subcomponent]:
        return self.subcomponents
    
    def __contains__(self, item: str) -> bool:
        return self.__getitem__(item) is not None
    
    def __getitem__(self, item: str) -> typing.Optional[subcomponent]:
        for c in self.subcomponents:
            if c.name == item:
                return c
        return None

@dataclasses.dataclass
class module(data_struct.tree.tree):
    name: str
    components: list[component]
    

    def __contains__(self, item: str) -> bool:
        return self.__getitem__(item) is not None
    
    def __getitem__(self, item: str) -> typing.Optional[component]:
        for c in self.components:
            if c.name == item:
                return c
        return None
    
    def children(self) -> list[component]:
        return self.components
    
@dataclasses.dataclass
class macro_module_info:
    key: key
    version: int | tuple[int, int]
    

class module_table:
    modules: list[module]
    
    def __init__(self):
        self.modules = []
    
    def __contains__(self, item: str | key) -> bool:
        return self.__getitem__(item) is not None
    
    def __getitem__(self, item: str | key) -> typing.Optional[module | subcomponent]:
        if isinstance(item, str):
            for m in self.modules:
                if m.name == item:
                    return m
            return None
        m = self.__getitem__(item.module)
        c = m.__getitem__(item.component)
        return c.__getitem__(item.subcomponent)
        
                