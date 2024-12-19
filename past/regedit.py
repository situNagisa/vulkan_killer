from typing import TypeVar, Generic

# 定义一个类型变量 T
T = TypeVar('T')


class regedit(Generic[T]):
    _data: dict[str, T]
    
    def __init__(self):
        self._data = {}
    
    def has(self, name: str) -> T:
        return name in self._data.keys()
    
    def set(self, name: str, value: T) -> None:
        assert not self.has(name)
        self._data[name] = value
    
    def get(self, name: str) -> T:
        assert self.has(name)
        return self._data[name]
    
    def get_or_none(self, name: str) -> T:
        if not self.has(name):
            return None
        return self.get(name)
    
    @property
    def underlying_data(self):
        return self._data

