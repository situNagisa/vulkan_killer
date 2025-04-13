import clang.cindex as CX
import cProfile

import logging


def main():
    logging.basicConfig(level=logging.DEBUG,  # 设置日志级别
                        format='%(name)s::%(levelname)s::%(message)s',  # 设置日志输出格式
                        handlers=[logging.StreamHandler()])  # 设置输出到控制台
    
    file = './test.h'
    # file = './vulkan/vulkan_core.h'
    # file = './vulkan_core.h'
    index = CX.Index.create(excludeDecls=False)
    tu = index.parse(file,
                     args=['-DVKAPI_PTR=__stdcall'],
                     options=CX.TranslationUnit.PARSE_DETAILED_PROCESSING_RECORD,
                     )
    
    def traverse(node: CX.Cursor, prefix="", is_last=True):
        branch = "└──" if is_last else "├──"
        text = f"{str(node.kind).removeprefix('CursorKind.')}: {node.spelling}"
        
        if node.kind == CX.CursorKind.INTEGER_LITERAL:
            value = list(node.get_tokens())[0].spelling
            text = f"{text}{value}"
        if node.kind == CX.CursorKind.MACRO_DEFINITION:
            if not node.spelling.startswith('_'):  # Exclude internal macros
                print(f"MACRO: {node.spelling}")
                print([token.spelling for token in node.get_tokens()])
        elif node.kind == CX.CursorKind.MACRO_INSTANTIATION:
            print(f"MACRO_INSTANTIATION: {node.spelling}")
            print([token.spelling for token in node.get_tokens()])
        
        # print(f"{prefix}{branch} {text}")
        new_prefix = prefix + ("    " if is_last else "│   ")
        children: list[CX.Cursor] = list(node.get_children())
        
        for child in children:
            traverse(child, new_prefix, child is children[-1])
    
    cursor: CX.Cursor = tu.cursor
    traverse(cursor)
    
    


if __name__ == '__main__':
    profiler = cProfile.Profile()
    profiler.enable()  # 开始性能分析
    main()
    profiler.disable()  # 停止性能分析
    
    profiler.dump_stats("profile_output.prof")
