from dataclasses import dataclass

from .declaration import block
from .name import name_introducer
from .symbol import symbol_sequence


@dataclass
class alias(block, name_introducer):
	from .name import name as _name
	from .type import type_id as _type_id
	
	identifier: _name
	attribute: list[str]
	type_id: _type_id
	
	def introduced_name(self) -> _name:
		return self.identifier
	
	def export_symbol_seq(self, table) -> symbol_sequence:
		from .symbol import symbol, category
		from .type import type_id as _type_id
		
		result: symbol_sequence = symbol_sequence()
		result.append(
			symbol(
				type_id=self.type_id,
				category=category.type,
				mangling=self.identifier,
				name=self.identifier,
				initializer=None
				)
			)
		for spe in self.type_id.decl_specifier_seq:
			if not isinstance(spe, name_introducer):
				continue
			result.append(symbol(
				type_id=_type_id(decl_specifier_seq=[spe]),
				category=category.type,
				mangling=spe.introduced_name(),
				name=spe.introduced_name(),
				initializer=None
			))
		
		return result
