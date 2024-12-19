from dataclasses import dataclass

from .specifier import typed, _keyword_specifier


class const(typed, _keyword_specifier):
    pass


class volatile(typed, _keyword_specifier):
    pass