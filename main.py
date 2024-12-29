import os.path

import clang.cindex as CX
import cProfile

from vk.c.parser import parse
# from generator import formatter
from vk.c import program as vkp
from vk.cpp.from_c import parse_c_program
import vk.cpp.generator
import vk.cpp.mangle
import vk.cpp.module
import vk.c.module

import logging

def main():
    logging.basicConfig(level=logging.DEBUG,  # 设置日志级别
                        format='%(name)s::%(levelname)s::%(message)s',  # 设置日志输出格式
                        handlers=[logging.StreamHandler()])  # 设置输出到控制台
    
    # file = './test.h'
    # file = './vulkan/vulkan_core.h'
    file = './vulkan_core.h'
    index = CX.Index.create(excludeDecls=True)
    tu = index.parse(file,
                     args=['-DVKAPI_PTR=__stdcall'])  # options=CX.TranslationUnit.PARSE_DETAILED_PROCESSING_RECORD)
    logging.info(f"parse file {file} successfully!")
    
    stmts = parse(file, tu.cursor)
    
    vk_c_symbol_table = vkp.collect_symbol_table(stmts)
    logging.info(f"cast vulkan to c program successfully")
    
    table, infos = vk.c.module.module_struct(file)
    module_keys = vk.cpp.module.classify_module(infos, vk_c_symbol_table)
    
    vkpp_symbol_table = parse_c_program(module_keys, vk_c_symbol_table)
    logging.info(f"cast c program to cpp symbols successfully")
    
    api = 'vulkan_killer'
    
    vk.cpp.mangle.mangle(api, vkpp_symbol_table)
    logging.info(f"mangle cpp symbols successfully")
    
    vk.cpp.module.make_module_table(table, vkpp_symbol_table)
    
    generates = vk.cpp.generator.generate(api, [info[1].key for info in infos], table, vkpp_symbol_table)
    for g in generates:
        os.makedirs(os.path.dirname(g.file), exist_ok=True)
        with open(g.file, 'w') as f:
            f.write(g.code)
            f.write('\n')
        logging.info(f"write result to {g.file}")
        
    

if __name__ == '__main__':
    profiler = cProfile.Profile()
    profiler.enable()  # 开始性能分析
    main()
    profiler.disable()  # 停止性能分析
    
    profiler.dump_stats("profile_output.prof")
