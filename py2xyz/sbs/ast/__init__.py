
import ast
import abc
import enum

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

class Statement(ast.AST,abc.ABC):
    pass

class Output(Statement):
    _fields = (
        'expression',
    )


class Expression(ast.AST, abc.ABC):
    pass

# experimental
class Reference(Expression):
    _fields = (
        'to',
    )

class Get(Expression):
    _fields = (
        'symbol',
    )

class BinaryOperation(Expression):
    _fields = (
        'left',
        'operator',
        'right',
    )

class Constant(Expression):
    _fields = (
        'value',
    )

class NumericalOperator(enum.Enum):
    Add  = enum.auto()
    Sub  = enum.auto()
    Mult = enum.auto()
    Div  = enum.auto()
    Mod  = enum.auto()
    Pow  = enum.auto()

class BooleanOperator(enum.Enum):
    And  = enum.auto()
    Or   = enum.auto()

class UnaryOperator(enum.Enum):
    Not = enum.auto()
    Sub = enum.auto()
