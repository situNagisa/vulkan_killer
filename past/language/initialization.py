from dataclasses import dataclass


class initializer:
    pass

@dataclass
class copy(initializer):
    from .expression import expression as _expression
    
    expression: _expression
    

class list(initializer):
    pass


class aggregate(list):
    pass


class direct(initializer):
    pass

class clauses:
    pass
