import abc
import typing

class tree(abc.ABC):
    
    @abc.abstractmethod
    def children(self) -> typing.Iterable:
        pass
    
    @staticmethod
    def filter_tree(iterable: typing.Iterable):
        return filter(lambda x: isinstance(x, tree), iterable)
    
    def grandchildren(self):
        for child in tree.filter_tree(self.children()):
            for grandchild in child.children():
                yield grandchild
    
    def layers(self):
        def chain(iterable: typing.Iterable[tree]) -> typing.Iterable:
            for element in iterable:
                for element_element in element.children():
                    yield element_element
                    
        queue_trees: typing.Iterable[tree] = [self]
        while queue_trees:
            queue = chain(queue_trees)
            yield queue
            queue_trees = tree.filter_tree(queue)
    
    def visit(self):
        for child in self.children():
            yield child
            if isinstance(child, tree):
                for grandchild in child.visit():
                    yield grandchild
