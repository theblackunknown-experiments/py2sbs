
import ast
import abc
import enum

from py2xyz.ir.ast import (
    Assign                    as IRAssign,
    Attribute                 as IRAttribute,
    BinaryOperation           as IRBinaryOperation,
    Call                      as IRCall,
    Constant                  as IRConstant,
    Function                  as IRFunction,
    Module                    as IRModule,
    Parameter                 as IRParameter,
    TypedParameter            as IRTypedParameter,
    Reference                 as IRReference,
    Return                    as IRReturn,
    UnaryOperation            as IRUnaryOperation,

    TextTypes                 as IRTextTypes,
    LogicalTypes              as IRLogicalTypes,
    NumericalTypes            as IRNumericalTypes,

    ANY_TEXT_TYPES            as IR_ANY_TEXT_TYPES,
    ANY_LOGICAL_TYPES         as IR_ANY_LOGICAL_TYPES,
    ANY_INTEGRAL_TYPES        as IR_ANY_INTEGRAL_TYPES,
    ANY_VECTOR_INTEGRAL_TYPES as IR_ANY_VECTOR_INTEGRAL_TYPES,
    ANY_FLOAT_TYPES           as IR_ANY_FLOAT_TYPES,
    ANY_VECTOR_FLOAT_TYPES    as IR_ANY_VECTOR_FLOAT_TYPES,
    ANY_NUMERICAL_TYPES       as IR_ANY_NUMERICAL_TYPES,
    ANY_VECTOR_TYPES          as IR_ANY_VECTOR_TYPES,
    ANY_TYPES                 as IR_ANY_TYPES,
)

TextTypes      = IRTextTypes
LogicalTypes   = IRLogicalTypes
NumericalTypes = IRNumericalTypes

ANY_TEXT_TYPES = set(TextTypes)

ANY_LOGICAL_TYPES = set(LogicalTypes)

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

# TODO Scalar Multiplication

class Division(Operator):
    SIGNATURES = _REAL_BINARY_OPERATION_SIGNATURES

class Negation(Operator):
    SIGNATURES = _REAL_UNARY_OPERATION_SIGNATURES

# Linear Algebra & Maths +

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

class PowerOf2(Operator):
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

class Package(AST):
    _fields = (
        'description',
        'content',
    )

class Graph(AST, abc.ABC):
    pass

class GraphStatement(AST, abc.ABC):
    pass

class Output(GraphStatement):
    _fields = (
        'node',
    )

class FunctionGraph(Graph):
    _fields = (
        'identifier',
        'parameters',
        '_statements',
        'nodes',
        'outputs',
    )

class FunctionParameter(AST):
    _fields = (
        'identifier',
        'type',
        'value',
    )

class Node(AST, abc.ABC):
    pass

class FunctionNode(Node, abc.ABC):
    pass

class Get(FunctionNode, abc.ABC):
    _fields = (
        'variable',
    )

class GetFloat1(Get):
    pass

class GetFloat2(Get):
    pass

class GetFloat3(Get):
    pass

class GetFloat4(Get):
    pass

class ConstFloat4(FunctionNode):
    _fields = (
        'x',
        'y',
        'z',
        'w',
    )

class Swizzle2(FunctionNode):
    _fields = (
        '_0',
        '_1',
        'from_node',
    )

class Swizzle3(FunctionNode):
    _fields = (
        '_0',
        '_1',
        '_2',
        'from_node',
    )

class Swizzle4(FunctionNode):
    _fields = (
        '_0',
        '_1',
        '_2',
        '_3',
        'from_node',
    )

class Set(FunctionNode):
    _fields = (
        'value',
        'from_node'
    )

class Div(FunctionNode):
    _fields = (
        'a',
        'b'
    )
