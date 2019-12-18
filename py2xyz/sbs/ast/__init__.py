
import ast
import abc

class Package(ast.AST):
    _fields = (
        'description',
        'content',
    )

class Graph(ast.AST, abc.ABC):
    _fields = (
        'identifier',
        'attributes',
        'parameters',
        'nodes',
    )

class FunctionGraph(Graph):
    pass

class Parameter(ast.AST, abc.ABC):
    _fields = (
        'identifier',
        'type',
        'value',
    )
