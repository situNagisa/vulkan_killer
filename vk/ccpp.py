

cpp_keywords = {
    'alignas', 'alignof', 'and', 'and_eq', 'asm', 'atomic_cancel', 'atomic_commit', 'atomic_noexcept',
    'auto', 'bitand', 'bitor', 'bool', 'break', 'case', 'catch', 'char', 'char16_t', 'char32_t', 'class',
    'compl', 'concept', 'const', 'consteval', 'constexpr', 'constinit', 'continue', 'co_await',
    'co_return', 'co_yield', 'decltype', 'default', 'delete', 'do', 'double', 'dynamic_cast', 'else',
    'enum', 'explicit', 'export', 'extern', 'false', 'float', 'for', 'friend', 'goto', 'if', 'import',
    'inline', 'int', 'long', 'mutable', 'namespace', 'new', 'noexcept', 'not', 'not_eq', 'nullptr', 'operator',
    'or', 'or_eq', 'private', 'protected', 'public', 'reflexpr', 'register', 'reinterpret_cast', 'requires',
    'return', 'short', 'signed', 'sizeof', 'static', 'static_assert', 'static_cast', 'struct', 'switch',
    'synchronized',
    'template', 'this', 'thread_local', 'throw', 'true', 'try', 'typedef', 'typeid', 'typename', 'union',
    'unsigned',
    'using', 'virtual', 'void', 'volatile', 'wchar_t', 'while', 'xor', 'xor_eq'
}
def is_cpp_keyword(word):
    # 检查是否是关键字
    if word in cpp_keywords:
        return True
    return False

def is_cpp_fundamental_type(name: str) -> bool:
    words = name.split(' ')
    assert len(words)
    return words[-1] in ('void', 'int', 'long', 'float', 'double', 'short', 'char')


def is_stdint_type(t: str) -> bool:
    if t == 'size_t':
        return True
    if not t.endswith('_t'):
        return False
    for prefix in ('int8', 'int16', 'int32', 'int64', 'int'):
        if t.startswith(f'{prefix}_') or t.startswith(f'u{prefix}_'):
            return True
    return False



