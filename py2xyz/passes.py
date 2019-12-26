
import ast
import logging
import collections
from pprint import pformat

logger = logging.getLogger(__name__)

from py2xyz import TranspilerError

from py2xyz.ir import (
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

class Variable(collections.namedtuple('Variable', ['name', 'type'])):
    pass

class Pass(ast.NodeTransformer):
    def __init__(self):
        self.logger = logging.getLogger(f'{__name__}.{self.__class__.__name__}')

class ResolveIRParameterType(Pass):

    def visit_Parameter(self, node):
        known_type = next((
            type_symbol
            for type_symbol in IR_ANY_TYPES
            if type_symbol.value == node.annotation
        ), None)
        if known_type:
            return IRTypedParameter(
                identifier=node.identifier,
                type=known_type,
                annotation=node.annotation,
                expression=node.expression,
            )
        else:
            return node

class ShaderToyPass(Pass):

    ARGUMENT_FRAG_COORD = Variable('fragCoord', IRNumericalTypes.Float2)
    ARGUMENT_FRAG_COLOR = Variable('fragColor', IRNumericalTypes.Float4)

# TODO deprecated in favor of optimization pass to resolve GLSL in/out/inout
class ShaderToyImageEntryPoint(ShaderToyPass):

    EXPECTED_ARGUMENTS = (
        ShaderToyPass.ARGUMENT_FRAG_COORD,
        ShaderToyPass.ARGUMENT_FRAG_COLOR,
    )

    def visit_Function(self, node):
        if node.identifier != 'mainImage':
            self.logger.debug(f'function is not the image entry point: {node.identifier}')
            return node

        are_expected_arguments = all(
            next((
                True
                for arg in node.arguments
                if isinstance(arg, IRTypedParameter)
                if (arg.identifier, arg.type) == expected_arg
            ), False)
            for expected_arg in self.EXPECTED_ARGUMENTS
        )

        if not are_expected_arguments:
            raise TranspilerError(f'Expected arguments not found: {self.EXPECTED_ARGUMENTS}', node)

        return IRFunction(
            identifier=node.identifier,
            arguments=[
                arg
                for arg in node.arguments
                if (arg.identifier, arg.type) != self.ARGUMENT_FRAG_COLOR
            ],
            body=[
                IRAssign(
                    identifier=self.ARGUMENT_FRAG_COLOR.name,
                    expression=IRCall(
                        func=self.ARGUMENT_FRAG_COLOR.type,
                        args=[ IRConstant(value=0.0) ] * 4,
                        keywords=[],
                    )
                )
            ] + node.body + [
                IRReturn(
                    expression=IRReference(variable=self.ARGUMENT_FRAG_COLOR.name)
                )
            ],
            returns=self.ARGUMENT_FRAG_COLOR.type,
        )

class GLSLPass(Pass):

    LOOKUP = {
        'float' : IRNumericalTypes.Float1,
        'vec2'  : IRNumericalTypes.Float2,
        'vec3'  : IRNumericalTypes.Float3,
        'vec4'  : IRNumericalTypes.Float4,
        'int'   : IRNumericalTypes.Integer1,
        'ivec2' : IRNumericalTypes.Integer2,
        'ivec3' : IRNumericalTypes.Integer3,
        'ivec4' : IRNumericalTypes.Integer4,
    }

class ResolveGLSLParameterType(GLSLPass):

    def visit_Parameter(self, node):
        if node.annotation in self.LOOKUP:
            return IRTypedParameter(
                identifier=node.identifier,
                type=self.LOOKUP[node.annotation],
                annotation=node.annotation,
                expression=node.expression,
            )
        else:
            return node

class ResolveGLSLTypeConstructor(GLSLPass):

    def visit_Call(self, node):
        irtype = self.LOOKUP.get(node.function, None)
        if irtype is None:
            self.logger.debug(f'not a type constructor: {node.function}')
            return node

        is_args_constant_expression = all(
            isinstance(_, IRConstant)
            for _ in node.args
        )

        if not is_args_constant_expression:
            self.logger.debug(f'args are not constexpr: {pformat([dump(_) for _ in node.args])}')
            return node

        assert not node.kwargs

        return IRCall(
            function=irtype,
            args=node.args,
            kwargs=node.kwargs,
        )

DEFAULTS = [
    ResolveIRParameterType,
    ResolveGLSLParameterType,
    ResolveGLSLTypeConstructor,
    ShaderToyImageEntryPoint,
]
