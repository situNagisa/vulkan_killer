import typing
from dataclasses import dataclass


@dataclass
class bit_field:
    from .initialization import initializer as _initializer
    identifier: str
    attribute: list[str]
    width: str
    initializer: typing.Optional[_initializer]

