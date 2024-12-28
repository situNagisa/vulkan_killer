import typing
from typing import TypeVar, Generic


from .specifier import specifier, typed
from .name import name

# 定义一个类型变量 T
T = TypeVar('T')

def cv_typed_only(seq: list[specifier]) -> list[typed]:
    return list(filter(lambda x: isinstance(x, typed), seq))

def typed_only(seq: list[specifier]) -> list[typed]:
    from .cv import const, volatile
    return list(filter(lambda x: isinstance(x, typed) and not isinstance(x, const) and not isinstance(x, volatile), seq))

def get_specifier_by_type(seq: list[specifier], t: Generic[T]) -> list[T]:
    return list(filter(lambda x: isinstance(x, t), seq))

def get_one_specifier_by_type(seq: list[specifier], t: Generic[T]) -> typing.Optional[T]:
    s = get_specifier_by_type(seq, t)
    if not len(s):
        return None
    assert len(s) == 1
    return s[0]

def get_ref_specifier(seq: list[specifier]):
    from .specifier import declared_type, elaborated_type
    return get_one_specifier_by_type(seq, declared_type | elaborated_type)

def get_ref_name(seq: list[specifier]) -> name:
    s = get_ref_specifier(seq)
    from .specifier import declared_type, elaborated_type
    if isinstance(s, declared_type):
        return s.name
    if isinstance(s, elaborated_type):
        return s.identifier.name
    raise 'fuck you'
