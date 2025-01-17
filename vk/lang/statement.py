from dataclasses import dataclass

import past.language.symbol

from .category import stmt as _stmt
from .category import c_symbol as _c_symbol
from .category import cpp_symbol as _cpp_symbol
from .category import mangling as _mangling

@dataclass
class plus_plus:
    from .module import key as _key
    
    module_key: _key
    cpp_category: _cpp_symbol
    mangling_category: _mangling
    symbol: past.language.symbol.symbol

@dataclass
class vk:
    location: past.language.location.source_location
    symbol: past.language.symbol.symbol
    
    @property
    def stmt_category(self) -> _stmt:
        return _stmt.symbol_be_declared_on(self.symbol)
    
    @property
    def c_category(self) -> _c_symbol:
        return _c_symbol.create(self.stmt_category, self.symbol)
    