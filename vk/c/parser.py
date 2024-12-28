import typing

from past import language as cpp
import past.language.declarator
import past.language.class_
import past.language.function
import past.language.enum
import past.language.statement
import past.language.location
import clang.cindex as cci
import os

def _get_location(file: str) -> str:
    return os.path.normpath(os.path.abspath(file))


def _is_expression_cursor(kind: cci.CursorKind) -> bool:
    return cci.CursorKind.UNEXPOSED_EXPR.value <= kind.value <= cci.CursorKind.OBJC_AVAILABILITY_CHECK_EXPR.value


def _is_decl_cursor(kind: cci.CursorKind) -> bool:
    return cci.CursorKind.UNEXPOSED_DECL.value <= kind.value <= cci.CursorKind.TYPEDEF_DECL.value


def _create_declarator_list(declarator: cpp.declarator.declarator) -> list[cpp.declarator.declarator]:
    if isinstance(declarator, cpp.declarator.name) or isinstance(declarator, cpp.declarator.abstract):
        return [declarator]
    if isinstance(declarator, cpp.declarator.pointer) or isinstance(declarator, cpp.declarator.array) or isinstance(
            declarator, cpp.function.declarator):
        return [declarator] + _create_declarator_list(declarator.declarator)
    raise 'fuck you'


def _reverse_declarator(declarator: cpp.declarator.declarator) -> cpp.declarator.declarator:
    l = _create_declarator_list(declarator)
    assert isinstance(l[-1], cpp.declarator.name) or isinstance(l[-1], cpp.declarator.abstract)
    l = [l[-1]] + l[:-1]
    for prev, curr in zip(l[:-1], l[1:]):
        assert isinstance(curr, cpp.declarator.pointer) or isinstance(curr, cpp.declarator.array) or isinstance(
            curr, cpp.function.declarator)
        curr.declarator = prev
    return l[-1]


def _create_declarator_impl(cursor: cci.Cursor) -> tuple[typing.Optional[cpp.declarator.declarator], list[cci.Cursor]]:
    children: list[cci.Cursor] = list(cursor.get_children())
    
    if cursor.kind in [cci.CursorKind.ENUM_DECL, cci.CursorKind.STRUCT_DECL, cci.CursorKind.UNION_DECL]:
        return None, children
    
    declarator = _create_reversed_declarator(cursor.type if cursor.kind != cci.CursorKind.TYPEDEF_DECL else cursor.underlying_typedef_type)
    
    if declarator is None:
        return None, children
    
    declarator = _reverse_declarator(declarator)
    
    # if cursor.kind in [cci.CursorKind.VAR_DECL, cci.CursorKind.FIELD_DECL]:
    #     if len(children) and children[0].kind == cci.CursorKind.TYPE_REF:
    #         children = children[1:]
    
    id: cpp.declarator.name | cpp.declarator.abstract = cpp.declarator.name(
        identifier=cpp.name.name(
            spelling=cursor.spelling,
            namespace=[],
        ),
    ) if cursor.spelling else cpp.declarator.abstract()
    if isinstance(declarator, cpp.declarator.abstract):
        if len(children) and children[0].kind == cci.CursorKind.TYPE_REF:
            children = children[1:]
        return id, children
    curr = declarator
    while True:
        assert isinstance(curr, cpp.declarator.pointer) or isinstance(curr, cpp.declarator.array) or isinstance(
            curr, cpp.function.declarator)
        if isinstance(curr, cpp.declarator.array):
            if len(children) and children[0].kind == cci.CursorKind.TYPE_REF:
                children = children[1:]
            assert children[0].kind == cci.CursorKind.INTEGER_LITERAL
            children = children[1:]
        elif isinstance(curr, cpp.function.declarator):
            if len(children) and children[0].kind == cci.CursorKind.TYPE_REF:
                children = children[1:]
            assert len(children) >= len(curr.parameter_list)
            for child, param in zip(children, curr.parameter_list):
                assert child.kind == cci.CursorKind.PARM_DECL
                assert isinstance(param, cpp.function.parameter)
                param.decl_specifier_seq = _create_specifier(child)
                param.declarator = _create_declarator(child)
            children = children[len(curr.parameter_list):]
        
        child = curr.declarator
        if isinstance(child, cpp.declarator.abstract):
            if len(children) and children[0].kind == cci.CursorKind.TYPE_REF:
                children = children[1:]
            curr.declarator = id
            break
        curr = child
    
    return declarator, children


def _create_declarator(cursor: cci.Cursor) -> typing.Optional[cpp.declarator.declarator]:
    return _create_declarator_impl(cursor)[0]


def _create_reversed_declarator(td: cci.Type) -> typing.Optional[cpp.declarator.declarator]:
    if td.kind == cci.TypeKind.CONSTANTARRAY:
        return cpp.declarator.array(
            attribute=[],
            declarator=_create_reversed_declarator(td.element_type),
            count=td.element_count,
        )
    elif td.kind == cci.TypeKind.POINTER:
        return cpp.declarator.pointer(
            attribute=[],
            declarator=_create_reversed_declarator(td.get_pointee()),
            const=cpp.cv.const() if td.is_const_qualified() else None,
            volatile=cpp.cv.volatile() if td.is_volatile_qualified() else None,
        )
    elif td.kind in [cci.TypeKind.FUNCTIONNOPROTO, cci.TypeKind.FUNCTIONPROTO]:
        parameter_list: list[cpp.function.parameter] = []
        if td.kind == cci.TypeKind.FUNCTIONPROTO:
            argument_types: list[cci.Type] = list(td.argument_types())
            for param in argument_types:
                parameter_list.append(cpp.function.parameter(
                    attribute=[],
                    this=False,
                    decl_specifier_seq=[],
                    declarator=cpp.declarator.abstract(),
                    initializer=None,
                ))
        return cpp.function.declarator(
            declarator=_create_reversed_declarator(td.get_result()),
            parameter_list=parameter_list,
            const=cpp.cv.const() if td.is_const_qualified() else None,
            volatile=cpp.cv.volatile if td.is_volatile_qualified() else None,
            noexcept=True,
            attribute=[],
        )
    return cpp.declarator.abstract()


def _create_init_declarator(cursor: cci.Cursor) -> list[cpp.init_declarator.init_declarator]:
    declarator, children = _create_declarator_impl(cursor)
    if declarator is None:
        return []
    initializer: typing.Optional[cpp.initialization.initializer] = None
    
    if len(children) and _is_expression_cursor(children[-1].kind):
        assert len(children) == 1
        tokens = list(children[-1].get_tokens())
        initializer = cpp.initialization.copy(
            expression=cpp.expression.literal(
                value_type=cpp.type.type_id(
                    decl_specifier_seq=[
                        cpp.specifier.fundamental(type=cpp.keyword.type.unsigned),
                        cpp.specifier.fundamental(type=cpp.keyword.type.long),
                        cpp.specifier.fundamental(type=cpp.keyword.type.long),
                    ],
                ),
                value=' '.join([token.spelling for token in tokens])
            )
        )
    
    return [cpp.init_declarator.init_declarator(
        declarator=declarator,
        initializer=initializer,
    )]


def _recurse_base_type(t: cci.Type) -> cci.Type:
    if t.kind is cci.TypeKind.POINTER:
        return _recurse_base_type(t.get_pointee())
    if t.kind in [cci.TypeKind.FUNCTIONNOPROTO, cci.TypeKind.FUNCTIONPROTO]:
        return _recurse_base_type(t.get_result())
    if t.kind is cci.TypeKind.CONSTANTARRAY:
        return _recurse_base_type(t.element_type)
    return t


def _create_specifier(cursor: cci.Cursor) -> list[cpp.specifier.specifier]:
    if cursor.kind in [cci.CursorKind.STRUCT_DECL, cci.CursorKind.UNION_DECL]:
        class_key: typing.Optional[cpp.keyword.class_] = None
        if cursor.kind == cci.CursorKind.STRUCT_DECL:
            class_key = cpp.keyword.class_.struct
        elif cursor.kind == cci.CursorKind.UNION_DECL:
            class_key = cpp.keyword.class_.union
        assert class_key
        assert cursor.type.kind in [cci.TypeKind.ELABORATED, cci.TypeKind.RECORD]
        
        words = cursor.spelling.split(' ')
        if cursor.type.kind == cci.TypeKind.ELABORATED:
            assert len(words) == 2
            assert words[0] == class_key.name
        
        head_name = cpp.name.name(namespace=[''], spelling=words[-1])
        c = cpp.class_.class_(
            attribute=[],
            class_key=class_key,
            head_name=head_name,
            bases=[],
            members=None,
        )
        
        if cursor.is_definition():
            c.members = []
            children: list[cci.Cursor] = list(cursor.get_children())
            for child in children:
                assert child.kind == cci.CursorKind.FIELD_DECL
                member_declarator_list: list[cpp.init_declarator.init_declarator | cpp.bit_field.bit_field] = []
                if child.is_bitfield():
                    member_declarator_list.append(cpp.bit_field.bit_field(
                        identifier=child.spelling,
                        attribute=[],
                        width=str(child.get_bitfield_width()),
                        initializer=None
                    ))
                else:
                    member_declarator_list.append(cpp.init_declarator.init_declarator(
                        declarator=_create_declarator(child),
                        initializer=None,
                    ))
                c.members.append(cpp.class_.member(
                    attribute=[],
                    decl_specifier_seq=_create_specifier(child),
                    member_declarator_seq=member_declarator_list,
                ))
        
        return [c]
    
    if cursor.kind == cci.CursorKind.ENUM_DECL:
        e = cpp.enum.enum_specifier(
            key=cpp.keyword.enum.enum,
            attribute=[],
            head_name=cpp.name.name(
                spelling=cursor.spelling,
                namespace=['']
            ),
            base=None,
            enumerator_list=None,
        )
        
        if cursor.is_definition():
            e.enumerator_list = []
            children: list[cci.Cursor] = list(cursor.get_children())
            for child in children:
                assert child.kind
                e.enumerator_list.append(cpp.enum.enumerator(
                    identifier=child.spelling,
                    value=str(child.enum_value),
                ))

        return [e]
    
    if _is_decl_cursor(cursor.kind):
        result: list[cpp.specifier.specifier] = []
        
        if cursor.kind == cci.CursorKind.TYPEDEF_DECL:
            result.append(cpp.specifier.typedef())
            base_type = _recurse_base_type(cursor.underlying_typedef_type)
        else:
            base_type = _recurse_base_type(cursor.type)
        
        words: list[str] = base_type.spelling.split(' ')
        if 'struct' in words:
            words.remove('struct')
        elif 'class' in words:
            words.remove('class')
        elif 'union' in words:
            words.remove('union')
        elif 'enum' in words:
            words.remove('enum')
        if 'const' in words:
            words.remove('const')
        if 'volatile' in words:
            words.remove('volatile')
        spelling: str = ' '.join(words)
        
        if 2 <= base_type.kind.value <= 23:
            result.append(cpp.specifier.fundamental(
                type=spelling
            ))
        elif base_type.kind is cci.TypeKind.AUTO:
            result.append(cpp.specifier.auto())
        elif base_type.kind is cci.TypeKind.ELABORATED:
            words: list[str] = base_type.spelling.split(' ')
            
            name = cpp.name.name(
                            namespace=[''],
                            spelling=spelling,
                        )
            from ..ccpp import is_stdint_type
            if is_stdint_type(name.spelling):
                name.namespace.append('std')
            
            if words[0] in ['struct', 'class', 'union', 'enum']:
                assert len(words) == 2
                if 'struct' == words[0]:
                    key = cpp.keyword.class_.struct
                elif 'class' == words[0]:
                    key = cpp.keyword.class_.class_
                elif 'union' == words[0]:
                    key = cpp.keyword.class_.union
                elif 'enum' == words[0]:
                    key = cpp.keyword.enum.enum
                else:
                    raise 'fuck you'
                result.append(cpp.specifier.elaborated_type(
                    key=key,
                    identifier=cpp.specifier.declared_type(name=name)
                ))
            else:
                result.append(cpp.specifier.declared_type(name=name))
        if base_type.is_const_qualified():
            result.append(cpp.cv.const())
        
        if base_type.is_volatile_qualified():
            result.append(cpp.cv.volatile())
        return result


def parse_statement(cursor: cci.Cursor) -> cpp.statement.statement:
    if _is_decl_cursor(cursor.kind):
        from past.language.declaration import simple
        
        result = simple(
            attribute=[],
            decl_specifier_seq=_create_specifier(cursor),
            init_declarator_seq=_create_init_declarator(cursor),
        )
        for decl in result.init_declarator_seq:
            decl.declarator.introduced_name().namespace = ['']
        return result


def parse(file: str, cursor: cci.Cursor) -> list[cpp.statement.location_statement]:
    result: list[cpp.statement.location_statement] = []
    
    assert cursor.kind == cci.CursorKind.TRANSLATION_UNIT
    assert isinstance(cursor.location, cci.SourceLocation)
    program_file: cpp.location.file = cpp.location.file(file)
    children = list(cursor.get_children())
    i = 0
    while i < len(children):
        child: cci.Cursor = children[i]
        extent: cci.SourceRange = child.extent
        start_location: cci.SourceLocation = extent.start
        end_location: cci.SourceLocation = extent.end
        if start_location.file is None:
            i += 1
            continue
        assert end_location.file is not None
        child_location = cpp.location.source_range(
            file=cpp.location.file(start_location.file.name),
            start=cpp.location.position(
                line=start_location.line,
                column=start_location.column
            ),
            end=cpp.location.position(
                line=end_location.line,
                column=end_location.column
            ),
        )
        if child_location.file != program_file:
            i += 1
            continue
        statement = parse_statement(child)
        result.append(cpp.statement.location_statement(
            extent=child_location,
            stmt=statement,
        ))
        i += 1
    
    return result
