import dataclasses


class A:
    aaa: int = 0
    
@dataclasses.dataclass
class B(A):
    bbb: int
    
    
i = B(
    bbb=2
)