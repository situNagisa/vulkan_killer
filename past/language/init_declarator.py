from dataclasses import dataclass
import typing


@dataclass
class init_declarator:
    from .declarator import declarator as _declarator
    from .initialization import initializer as _initializer
    declarator: _declarator
    initializer: typing.Optional[_initializer]