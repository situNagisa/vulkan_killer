import copy
import typing


class node:
    def __init__(self, name: str):
        self.name: str = name
        self.underlying_data: set[node] = set[node]()
    
    def __contains__(self, ns: str | list[str]) -> bool:
        if isinstance(ns, str):
            return self[ns] is not None
        assert len(ns)
        if ns[0] != self.name:
            return False
        if len(ns) < 2:
            return True
        for child in self.underlying_data:
            if ns[1:] in child:
                return True
        return False
    
    def __getitem__(self, key: str | list[str]):
        if isinstance(key, str):
            for n in self.underlying_data:
                if n.name == key:
                    return n
            return None
        assert len(key)
        if key[0] != self.name:
            return None
        key = key[1:]
        if not len(key):
            return self
        return self.__getitem__(key)
    
    def __setitem__(self, key: str, value):
        assert isinstance(value, node)
        for n in self.underlying_data:
            if n.name == key:
                self.underlying_data.remove(n)
                self.underlying_data.add(value)
                return
        raise 'fuck you'
    
    def __deepcopy__(self, memo):
        result = node(self.name)
        result.underlying_data = copy.deepcopy(self.underlying_data, memo)
        return result
    
    def __or__(self, other):
        assert isinstance(other, node)
        assert self.name == other.name
        result = copy.deepcopy(self)
        for child in other.underlying_data:
            if child.name not in result:
                result.underlying_data.add(child)
                continue
            result[child.name] = result[child.name] | child
        return result
    
    def add(self, new):
        assert isinstance(new, node)
        assert new.name not in self
        self.underlying_data.add(new)
    
    @staticmethod
    def create_from_namespace(namespace: list[str]):
        if not len(namespace):
            return None
        result = node(namespace[0])
        if len(namespace[1:]):
            result.add(node.create_from_namespace(namespace[1:]))
        return result
    
    def find_namespace_on(self, base: list[str], target: list[str]) -> list[str]:
        while not self.__contains__(base + target):
            base = base[:-1]
        return base
        