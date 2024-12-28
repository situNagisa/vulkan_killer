'''
statement
    declaration
        block
            simple
            type_alias
            using_declaration
'''
import typing
from dataclasses import dataclass


class statement:
    pass

@dataclass
class location_statement:
    from .location import source_location as _source_location
    from .location import source_range as _source_range
    extent: _source_range
    stmt: statement
    
    @property
    def location(self) -> _source_location:
        from .location import source_location
        return source_location(
            file=self.extent.file,
            position=self.extent.start,
        )
    

@dataclass
class expression(statement):
    from .expression import expression as _expression
    attribute: list[str]
    expression: _expression
    

@dataclass
class compound(statement):
    attribute: list[str]
    statement_seq: list[statement]

@dataclass
class selection(statement):
    pass

@dataclass
class if_(selection):
    attribute: list[str]
    constexpr: bool
    # init: typing.Optional
    condition: expression
    true_branch: statement
    else_branch: typing.Optional[statement]
    

@dataclass
class jump(statement):
    pass

@dataclass
class return_(jump):
    expression: typing.Optional[expression]
    
    
    