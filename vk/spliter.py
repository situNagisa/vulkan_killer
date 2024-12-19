import re


def _split_cat(words: list[str], callback) -> list[str]:
    result = []
    for word in words:
        result += callback(word)
    result2 = []
    for word in result:
        if len(word):
            result2.append(word)
    return result2


def _split_number(string: str) -> list[str]:
    matches = list(re.finditer(r"([a-zA-Z]+((\d[dD])|(\d+)))|(\b\d+)", string))
    # 用于存储匹配的部分和未匹配的部分
    # 用于存储按顺序排列的匹配和未匹配部分
    result = []
    
    # 上一个匹配的结束位置，用于找出未匹配的部分
    last_end = 0
    
    for match in matches:
        # 添加未匹配的部分
        if match.start() > last_end:
            result.append(string[last_end:match.start()])
        
        # 添加匹配的部分
        result.append(match.group(0))
        
        # 更新 last_end 为当前匹配的结束位置
        last_end = match.end()
    
    # 添加最后一个匹配后未匹配的部分
    if last_end < len(string):
        result.append(string[last_end:])
    
    return result


def _split_camel(string: str) -> list[str]:
    result = []
    current_chunk = string[0]
    
    def callback(prev_char, current_char):
        return prev_char.islower() and current_char.isupper()
    
    for i in range(1, len(string)):
        if callback(string[i - 1], string[i]):
            result.append(current_chunk)
            current_chunk = string[i]
        else:
            current_chunk += string[i]
    result.append(current_chunk)  # 最后一个分组
    
    return result


def split_identifier(t: str) -> list[str]:
    from .ccpp import is_stdint_type
    if is_stdint_type(t):
        return [t]
    return _split_cat(_split_cat(_split_cat([t],
                                            lambda s: s.split('_')),
                                 _split_number),
                      _split_camel
                      )