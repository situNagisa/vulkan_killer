import typing
from dataclasses import dataclass

from vk import ccpp


@dataclass
class name:
    namespace: list[str]
    spelling: str
    
    @property
    def qualified_name(self) -> str:
        if ccpp.is_cpp_fundamental_type(self.spelling):
            return self.spelling
        return qualified_name(self.spelling, self.namespace)
    
    def __eq__(self, other) -> bool:
        return self.qualified_name == other.qualified_name
    
    def __copy__(self):
        return name(self.namespace, self.spelling)
    
    def __deepcopy__(self, memo):
        import copy
        return name(copy.deepcopy(self.namespace, memo), copy.deepcopy(self.spelling, memo))
    
    def __hash__(self):
        return hash(self.qualified_name)


class name_introducer:
    from abc import abstractmethod as _abstractmethod
    
    @_abstractmethod
    def introduced_name(self) -> name:
        pass


def filter_introducer(range: typing.Iterable) -> list[name_introducer]:
    return list(filter(lambda item: isinstance(item, name_introducer), range))


def _is_sublist(lst1, lst2):
    # 遍历 lst1，检查是否有连续的子序列与 lst2 相同
    for i in range(len(lst1) - len(lst2) + 1):
        if lst1[i:i + len(lst2)] == lst2:
            return True
    return False


def base_namespace(target: list[str], current: list[str]) -> int:
    count = 0
    while count < min(len(target), len(current)) and target[count] == current[count]:
        count += 1
    return count


def relative_namespace(target: list[str], current: list[str]) -> list[str]:
    return target[base_namespace(target, current):]


def qualified_name(spelling: str, namespace: list[str]) -> str:
    result = ""
    for ns in namespace:
        result += f"{ns}::"
    result += spelling
    return result


def relative_name(n: name, namespace: list[str]) -> str:
    rn = relative_namespace(n.namespace, namespace)
    if rn == n.namespace or ([''] + rn == n.namespace):
        return qualified_name(n.spelling, n.namespace)
    return qualified_name(n.spelling, rn)
