import clang.cindex as CX
import cProfile

from vk.c.parser import parse
# from generator import formatter
from vk.c import program as vkp
from vk.cpp.from_c import parse_c_program
import vk.cpp.generator
import vk.cpp.mangle

import logging

def main():
    logging.basicConfig(level=logging.DEBUG,  # 设置日志级别
                        format='%(name)s::%(levelname)s::%(message)s',  # 设置日志输出格式
                        handlers=[logging.StreamHandler()])  # 设置输出到控制台
    
    # file = './test.h'
    file = './vulkan/vulkan_core.h'
    # file = './vulkan_core.h'
    index = CX.Index.create(excludeDecls=True)
    tu = index.parse(file,
                     args=['-DVKAPI_PTR=__stdcall'])  # options=CX.TranslationUnit.PARSE_DETAILED_PROCESSING_RECORD)
    logging.info(f"parse file {file} successfully!")
    
    program = vkp.program(parse(file, tu.cursor))
    logging.info(f"cast vulkan to c program successfully")
    
    result = parse_c_program(program)
    logging.info(f"cast c program to cpp symbols successfully")
    
    vk.cpp.mangle.mangle(result)
    logging.info(f"mangle cpp symbols successfully")
    
    output_file = "test_vulkan.h"
    code = vk.cpp.generator.generate(result)
    with open(output_file, 'w') as f:
        f.write(
            '#include <cstdint>\n'
            '#include <cstddef>\n'
            '#include <type_traits>\n'
            '#include <concepts>\n'
            '\n'
            'namespace vk {\n'
            '\ttemplate<::std::integral auto MaxEnum, ::std::integral auto MinEnum>\n'
            '\tstruct _calculate_enum_underlying_type\n'
            '\t{\n'
            '\t\tenum\n'
            '\t\t{\n'
            '\t\t\tmin_enum = MinEnum,\n'
            '\t\t\tmax_enum = MaxEnum,\n'
            '\t\t};\n'
            '\t\tusing type = ::std::underlying_type_t<decltype(max_enum)>;\n'
            '\t};\n'
            '\t\n'
            '\ttemplate<::std::integral auto MaxEnum, ::std::integral auto MinEnum = 0u>\n'
            '\tusing _calculate_enum_underlying_type_t = typename _calculate_enum_underlying_type<MaxEnum, MinEnum>::type;\n'
            '\t\n'
            '}\n'
            '\n'
        )
        f.write(code)
        f.write('\n')
    
    logging.info(f"write result to {output_file}")

if __name__ == '__main__':
    profiler = cProfile.Profile()
    profiler.enable()  # 开始性能分析
    main()
    profiler.disable()  # 停止性能分析
    
    profiler.dump_stats("profile_output.prof")
