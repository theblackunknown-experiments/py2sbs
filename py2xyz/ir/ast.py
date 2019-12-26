
import abc
import ast
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

class Operator(ast.AST, abc.ABC):
    def signatures():
        return self.SIGNATURES

_BOOLEAN_UNARY_OPERATION_SIGNATURES = [
    ( (_,), _ )
    for _ in ANY_LOGICAL_TYPES
]

_BOOLEAN_BINARY_OPERATION_SIGNATURES = [
    ( (_, _), _ )
    for _ in ANY_LOGICAL_TYPES
]

_FLOAT_BINARY_OPERATION_SIGNATURES = [
    ( (_, _), _ )
    for _ in { NumericalTypes.Float1 }
]

_REAL_BINARY_OPERATION_SIGNATURES = [
    ( (_, _), _ )
    for _ in ANY_NUMERICAL_TYPES
]

_NON_VECTOR_BINARY_OPERATION_SIGNATURES = [
    ( (_, _), _ )
    for _ in ANY_NUMERICAL_TYPES - ANY_VECTOR_TYPES
]

_VECTOR_BINARY_OPERATION_SIGNATURES = [
    ( (_, _), _ )
    for _ in ANY_VECTOR_TYPES
]

_FLOAT_UNARY_OPERATION_SIGNATURES = [
    ( (_,), _ )
    for _ in { NumericalTypes.Float1 }
]

_REAL_UNARY_OPERATION_SIGNATURES = [
    ( (_,), _ )
    for _ in ANY_NUMERICAL_TYPES
]

# Maths

class Addition(Operator):
    SIGNATURES = _REAL_BINARY_OPERATION_SIGNATURES

class Substraction(Operator):
    SIGNATURES = _REAL_BINARY_OPERATION_SIGNATURES

class Modulo(Operator):
    SIGNATURES = _REAL_BINARY_OPERATION_SIGNATURES

class Multiplication(Operator):
    SIGNATURES = _REAL_BINARY_OPERATION_SIGNATURES

class Division(Operator):
    SIGNATURES = _REAL_BINARY_OPERATION_SIGNATURES

class Negation(Operator):
    SIGNATURES = _REAL_UNARY_OPERATION_SIGNATURES

# Linear Algebra & Maths +
# NOTE Are thsoe really necessary ?
#   > We don't have math analysis yet
#   > Those can also represent by Call

class Dot(Operator):
    SIGNATURES = _VECTOR_BINARY_OPERATION_SIGNATURES

class Cross(Operator):
    SIGNATURES = _VECTOR_BINARY_OPERATION_SIGNATURES

class Modulus(Operator):
    SIGNATURES = _FLOAT_UNARY_OPERATION_SIGNATURES

class Floor(Operator):
    SIGNATURES = _FLOAT_UNARY_OPERATION_SIGNATURES

class Ceil(Operator):
    SIGNATURES = _FLOAT_UNARY_OPERATION_SIGNATURES

class Cos(Operator):
    SIGNATURES = _FLOAT_UNARY_OPERATION_SIGNATURES

class Sin(Operator):
    SIGNATURES = _FLOAT_UNARY_OPERATION_SIGNATURES

class SquareRoot(Operator):
    SIGNATURES = _FLOAT_UNARY_OPERATION_SIGNATURES

class NaturalLogarithm(Operator):
    SIGNATURES = _FLOAT_UNARY_OPERATION_SIGNATURES

class Logarithm2(Operator):
    SIGNATURES = _FLOAT_UNARY_OPERATION_SIGNATURES

class NaturalExponential(Operator):
    SIGNATURES = _FLOAT_UNARY_OPERATION_SIGNATURES

class Power(Operator):
    SIGNATURES = _FLOAT_BINARY_OPERATION_SIGNATURES

# Logicals

class And(Operator):
    SIGNATURES = _BOOLEAN_BINARY_OPERATION_SIGNATURES

class Or(Operator):
    SIGNATURES = _BOOLEAN_BINARY_OPERATION_SIGNATURES

class Not(Operator):
    SIGNATURES = _BOOLEAN_UNARY_OPERATION_SIGNATURES

# Comparison

class Equals(Operator):
    SIGNATURES = _NON_VECTOR_BINARY_OPERATION_SIGNATURES

# TODO >, >=, <, <=

class AST(ast.AST, abc.ABC):
    pass

class Statement(AST, abc.ABC):
    pass

class Expression(AST, abc.ABC):
    pass

class Module(AST):
    _fields = (
        'description',
        'content',
    )

class Parameter(AST):
    _fields = (
        'identifier',
        'annotation',
        'expression',
    )

class TypedParameter(AST):
    _fields = (
        'identifier',
        'type',
        'annotation',
        'expression',
    )

class Return(Statement):
    _fields = (
        'expression',
    )

class Assign(Statement):
    _fields = (
        'identifier',
        'expression',
    )

class Function(Statement):
    _fields = (
        'identifier',
        'arguments',
        'body',
        'returns',
    )

class OverloadedFunction(Function):
    _fields = (
        'identifier',
        'arguments',
        'body',
        'overloads',
    )

class Call(Expression):
    _fields = (
        'function',
        'args',
        'kwargs',
    )

class Constant(Expression):
    _fields = (
        'value',
    )

class Reference(Expression):
    _fields = (
        'variable',
    )

class Attribute(Expression):
    _fields = (
        'variable',
        'fields',
    )

class BinaryOperation(Expression):
    _fields = (
        'left',
        'operator',
        'right',
    )

class UnaryOperation(Expression):
    _fields = (
        'operator',
        'operand',
    )
