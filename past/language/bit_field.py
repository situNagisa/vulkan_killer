import typing
from dataclasses import dataclass

from .name import depender, name

@dataclass
class bit_field(depender):
    from .initialization import initializer as _initializer
    identifier: str
    attribute: list[str]
    width: str
    initializer: typing.Optional[_initializer]
    
    def get_depend_names(self) -> set[name]:
        if self.initializer is not None and isinstance(self.initializer, depender):
            return self.initializer.get_depend_names()
        return set[name]()

