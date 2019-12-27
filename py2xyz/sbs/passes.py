
import ast
import pprint
import logging
import itertools

logger = logging.getLogger(__name__)

from py2xyz import dump

from py2xyz import TranspilerError

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

from py2xyz.sbs.ast import (
    ConstFloat4               as SBSConstFloat4,
)

class Pass(ast.NodeTransformer):
    def __init__(self):
        self.logger = logging.getLogger(f'{__name__}.{self.__class__.__name__}')

class FoldPow2ExpressionPass(Pass):
    def visit_BinaryOperation(self, node):
        logger.debug(f'FoldPow2ExpressionPass - {dump(node)}')
        if node.operator.opcode is NonNativeNumericalOperator.Pow:
            # TODO fold constant pass before hand
            left = self.visit(node.left)

            if not isinstance(left, Constant):
                raise TranspilerError(f'Cannot fold pow in pow2 : left operand is not Constan', left)

            if left.value != 2:
                raise TranspilerError(f'Cannot fold pow in pow2 : left operand is not equals to 2', left)

            return UnaryOperation(
                operator=Operator(opcode=NativeUnaryOperator.Pow2),
                operand=node.right,
            )
        else:
            return node

class ResolveConstNode(Pass):

    LOOKUP_TABLE = {
        IRNumericalTypes.Float4: SBSConstFloat4,
    }

    def visit_Call(self, node):
        if node.function not in self.LOOKUP_TABLE:
            self.logger.debug(f'something else than a const node \n{dump(node)}')
            return node

        if not all(map(lambda _: isinstance(_, IRConstant), node.args)):
            self.logger.debug(f'arguments are not all constant \n{dump(node)}')
            return node

        sbsnodeclass = self.LOOKUP_TABLE[node.function]
        return sbsnodeclass(**{
            fieldname: constnode.value
            for fieldname, constnode in zip(sbsnodeclass._fields, node.args)
        })

DEFAULT_PRE_PASSES = [
    ResolveConstNode,
]

DEFAULT_POST_PASSES = [
    # ShaderToyIntrinsicPass,
    # ResolveParameterTypeFromDefaultValue,
    # FoldPow2ExpressionPass,
    # ResolveFunctionOverloadSetPass,
    # FlattenOverloadedFunctionsPass,
]
