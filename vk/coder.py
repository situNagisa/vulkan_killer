

def _namespace_indent(ns: list[str]) -> int:
    return max(0, len(ns) - 1)


class code:
    def __init__(self):
        self.data: str = ''
        self.ns: list[str] = ['']
    
    def _write_line(self, line: str = ''):
        self.data += '\t' * _namespace_indent(self.ns) + line + '\n'
    
    def write_line(self, lines: str = ''):
        for line in lines.split('\n'):
            self._write_line(line)
    
    def change_namespace(self, new_ns: list[str]):
        n = 0
        while n < min(len(self.ns), len(new_ns)) and self.ns[n] == new_ns[n]:
            n += 1
        pop_count, push_ns = len(self.ns) - n, new_ns[n:]
        while pop_count:
            line = '}'
            # if self.ns[-1] == 'c':
            #     line += '}'
            self.ns.pop()
            self.write_line(line)
            pop_count -= 1
        for ns in push_ns:
            line = f'namespace {ns}{{'
            # if ns == 'c':
            #     line += ' extern \"C\"{'
            self.write_line(line)
            self.ns.append(ns)
