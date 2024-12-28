from dataclasses import dataclass
import typing
from .name import depender, name


@dataclass
class init_declarator(depender):
    from .declarator import declarator as _declarator
    from .initialization import initializer as _initializer
    declarator: _declarator
    initializer: typing.Optional[_initializer]
    
    def get_depend_names(self) -> set[name]:
        result = set[name]()
        if isinstance(self.declarator, depender):
            result = result | self.declarator.get_depend_names()
        if self.initializer is not None and isinstance(self.initializer, depender):
            result = result | self.initializer.get_depend_names()
        return result