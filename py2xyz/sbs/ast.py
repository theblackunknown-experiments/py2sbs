
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

class ConstFloat1(FunctionNode):
    _fields = (
        'x',
    )

class ConstFloat2(FunctionNode):
    _fields = (
        'x',
        'y',
    )

class ConstFloat3(FunctionNode):
    _fields = (
        'x',
        'y',
        'z',
    )

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

class BinaryOperation(FunctionNode, abc.ABC):
    _fields = (
        'a',
        'b'
    )

class Add(BinaryOperation):
    pass

class Sub(BinaryOperation):
    pass

class Mul(BinaryOperation):
    pass

class Div(BinaryOperation):
    pass
