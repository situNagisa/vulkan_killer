import typing

from .specifier import typed
from .name import name, depender, collect_depend_name_from_iterable

class type_id(depender):
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
	
	def get_depend_names(self) -> set[name]:
		result = collect_depend_name_from_iterable(self.decl_specifier_seq)
		if isinstance(self.declarator, depender):
			result = result | self.declarator.get_depend_names()
		return result
