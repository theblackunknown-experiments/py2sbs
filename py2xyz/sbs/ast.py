
import ast
import abc
import enum

class TextTypes(enum.Enum):
    String = 'str'

ANY_TEXT_TYPES = set(TextTypes)

class LogicalTypes(enum.Enum):
    Boolean = 'bool'

ANY_LOGICAL_TYPES = set(LogicalTypes)

class NumericalTypes(enum.Enum):
    Integer1 = 'int'
    Integer2 = 'int2'
    Integer3 = 'int3'
    Integer4 = 'int4'
    Float1   = 'float'
    Float2   = 'float2'
    Float3   = 'float3'
    Float4   = 'float4'

ANY_NUMERICAL_TYPES = set(NumericalTypes)

ANY_TYPES = ANY_TEXT_TYPES | ANY_LOGICAL_TYPES | ANY_NUMERICAL_TYPES

class NumericalOperator(enum.Enum):
    Add  = enum.auto()
    Sub  = enum.auto()
    Mult = enum.auto()
    Div  = enum.auto()
    Mod  = enum.auto()
    Pow  = enum.auto()

    def overloads(self):
        if self in {NumericalOperator.Add, NumericalOperator.Mod, NumericalOperator.Pow}:
            return (
                (_, _ )
                for _ in NumericalTypes
            )
        else:
            raise NotImplementedError(f'Overloads not implemented for {self}')

class BooleanOperator(enum.Enum):
    And  = enum.auto()
    Or   = enum.auto()

class UnaryOperator(enum.Enum):
    Not = enum.auto()
    Sub = enum.auto()

class AST(ast.AST, abc.ABC):
    pass

class Package(AST):
    _fields = (
        'description',
        'content',
    )

class Graph(AST, abc.ABC):
    _fields = (
        'identifier',
        'attributes',
        'parameters',
        'nodes',
    )

class FunctionGraph(Graph):
    pass

class OverloadedFunctionGraph(FunctionGraph):
    _fields = (
        'identifier',
        'attributes',
        'parameters',
        'nodes',
        'overloads',
    )

class Parameter(AST, abc.ABC):
    _fields = (
        'identifier',
        'type',
        'value',
    )

class Statement(AST,abc.ABC):
    pass

class Output(Statement):
    _fields = (
        'expression',
    )


class Expression(AST, abc.ABC):
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
