import os.path
from dataclasses import dataclass
from functools import total_ordering

class file:
    def __init__(self, path: str):
        self._path: str = os.path.normpath(os.path.abspath(path))
    
    def path(self) -> str:
        return self._path
    
    def __eq__(self, other) -> bool:
        return self.path() == other.path()

@total_ordering
@dataclass
class position:
    line: int
    column: int
    
    def __eq__(self, other) -> bool:
        return self.line == other.line and self.column == other.column
    
    def __lt__(self, other) -> bool:
        if self.line != other.line:
            return self.line < other.line
        return self.column < other.column
    

@dataclass
class source_location:
    file: file
    position: position
    
@dataclass
class source_range:
    file: file
    start: position
    end: position
    
    def __init__(self, file: file, start: position, end: position):
        self.file = file
        self.start = start
        self.end = end
        assert start <= end
    
    
    