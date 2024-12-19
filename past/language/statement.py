'''
statement
    declaration
        block
            simple
            type_alias
            using_declaration
'''
from dataclasses import dataclass


class statement:
    pass

@dataclass
class expression_statement(statement):
    from .expression import expression as _expression
    attribute: list[str]
    expression: _expression
    
    