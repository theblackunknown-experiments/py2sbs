
import ast
import abc
import enum

class TextTypes(enum.Enum):
    String = 's'

ANY_TEXT_TYPES = set(TextTypes)

class LogicalTypes(enum.Enum):
    Boolean = 'b1'

ANY_LOGICAL_TYPES = set(LogicalTypes)

class NumericalTypes(enum.Enum):
    Integer1 = 'i1'
    Integer2 = 'i2'
    Integer3 = 'i3'
    Integer4 = 'i4'
    Float1   = 'f1'
    Float2   = 'f2'
    Float3   = 'f3'
    Float4   = 'f4'

ANY_INTEGRAL_TYPES = {
    NumericalTypes.Integer1,
    NumericalTypes.Integer2,
    NumericalTypes.Integer3,
    NumericalTypes.Integer4,
}

ANY_VECTOR_INTEGRAL_TYPES = {
    NumericalTypes.Integer2,
    NumericalTypes.Integer3,
    NumericalTypes.Integer4,
}

ANY_FLOAT_TYPES = {
    NumericalTypes.Float1,
    NumericalTypes.Float2,
    NumericalTypes.Float3,
    NumericalTypes.Float4,
}

ANY_VECTOR_FLOAT_TYPES = {
    NumericalTypes.Float2,
    NumericalTypes.Float3,
    NumericalTypes.Float4,
}

ANY_NUMERICAL_TYPES = ANY_INTEGRAL_TYPES | ANY_FLOAT_TYPES

ANY_VECTOR_TYPES = ANY_VECTOR_INTEGRAL_TYPES | ANY_VECTOR_FLOAT_TYPES

ANY_TYPES = ANY_TEXT_TYPES | ANY_LOGICAL_TYPES | ANY_NUMERICAL_TYPES

class NonNativeNumericalOperator(enum.Enum):
    Pow  = enum.auto()

    def overloads(self):
        if self in {NonNativeNumericalOperator.Pow}:
            return (
                (_, _ )
                for _ in ANY_NUMERICAL_TYPES
            )
        else:
            raise NotImplementedError(f'Overloads not implemented for {self}')

class NativeBinaryOperator(enum.Enum):
    Add        = enum.auto()
    Sub        = enum.auto()
    Mult       = enum.auto()
    MultScalar = enum.auto()
    Div        = enum.auto()
    Mod        = enum.auto()
    Dot        = enum.auto()
    Cross      = enum.auto()
    And        = enum.auto()
    Or         = enum.auto()
    Equals     = enum.auto()
    NotEquals  = enum.auto()

    def overloads(self):
        symbols = NativeBinaryOperator
        if self in {symbols.Add, symbols.Mod, symbols.Mult, symbols.Div}:
            return (
                (_, _)
                for _ in ANY_NUMERICAL_TYPES
            )
        elif self in {symbols.Equals, symbols.NotEquals}:
            return (
                (_, _)
                for _ in {NumericalTypes.Float1, NumericalTypes.Integer1}
            )
        elif self in {symbols.MultScalar}:
            return (
                (_, NumericalTypes.Float1)
                for _ in {NumericalTypes.Float2, NumericalTypes.Float3, NumericalTypes.Float4}
            )
        elif self in {symbols.Dot, symbols.Cross}:
            return (
                (_, _)
                for _ in {NumericalTypes.Float2, NumericalTypes.Float3, NumericalTypes.Float4}
            )
        elif self in {symbols.And, symbols.Or}:
            return (
                (LogicalTypes.Boolean, LogicalTypes.Boolean)
            )
        else:
            raise NotImplementedError(f'Overloads not implemented for {self}')

class NativeUnaryOperator(enum.Enum):
    Not  = enum.auto()
    Sub  = enum.auto()
    Pow2 = enum.auto()

    def overloads(self):
        if self in {NativeUnaryOperator.Pow2}:
            return ANY_FLOAT_TYPES
        elif self in {NativeUnaryOperator.Not}:
            return ANY_LOGICAL_TYPES
        else:
            raise NotImplementedError(f'Overloads not implemented for {self}')

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

class Statement(AST, abc.ABC):
    pass

class Output(Statement):
    _fields = (
        'expression',
    )

class Set(Statement):
    _fields = (
        'identifier',
        'expression',
    )

class Expression(AST, abc.ABC):
    pass

class Get(Expression):
    _fields = (
        'identifier',
    )

class Call(Expression):
    _fields = (
        'url',
        'operands',
        'package',
    )

class Operator(AST):
    _fields = (
        'opcode',
    )

class BinaryOperation(Expression):
    _fields = (
        'left',
        'right',
        'operator',
    )

class UnaryOperation(Expression):
    _fields = (
        'operator',
        'operand',
    )

class Constant(Expression):
    _fields = (
        'value',
    )
