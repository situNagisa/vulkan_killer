import typing

from .specifier import specifier, typed


class type_id:
	from .declarator import declarator as _declarator
	
	decl_specifier_seq: list[typed]
	declarator: _declarator
	
	def __init__(self, decl_specifier_seq: list[typed], declarator: typing.Optional[_declarator] = None):
		from .declarator import get_identifier_declarator
		from .declarator import abstract
		declarator = declarator if declarator is not None else abstract()
		assert isinstance(get_identifier_declarator(declarator), abstract)
		self.decl_specifier_seq = decl_specifier_seq
		self.declarator = declarator


def as_typed_specifier_seq(seq: list[specifier]) -> list[typed]:
	return list(filter(lambda x: isinstance(x, typed), seq))
