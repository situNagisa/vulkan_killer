from . import language as cpp
import past.language.statement


def is_typedef_declaration(declaration: cpp.statement.statement) -> bool:
    if not isinstance(declaration, cpp.declaration.simple):
        return False
    if not len(declaration.decl_specifier_seq):
        return False
    if not any([isinstance(s, cpp.specifier.typedef) for s in declaration.decl_specifier_seq]):
        return False
    s_seq = [s for s in declaration.decl_specifier_seq if not isinstance(s, cpp.specifier.typedef)]
    if not all([isinstance(s, cpp.specifier.typed) for s in s_seq]):
        return False
    return True
