import enum


class keyword:
    pass


class keyword_enum(keyword, enum.Enum):
    @property
    def name(self) -> str:
        if isinstance(self.value, str):
            return self.value
        result = super().name
        if result.endswith('_'):
            return result[:-1]
        return result


class class_(keyword_enum):
    class_ = 'class'
    struct = 'struct'
    union = 'union'


class enum(keyword_enum):
    enum = 'enum'
    enum_class = 'enum class'
    enum_struct = 'enum struct'


class access(keyword_enum):
    private = 'private'
    protected = 'protected'
    public = 'public'
    
    
class type(keyword_enum):
    char = 0
    char8_t = 1
    char16_t = 2
    char32_t = 3
    wcahr_t = 4
    bool = 5
    short = 6
    int = 7
    long = 8
    signed = 9
    unsigned = 10
    float = 11
    double = 12
    void = 13