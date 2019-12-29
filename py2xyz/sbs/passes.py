
import ast
import logging
import itertools

from pprint import pformat

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
    ConstFloat4    as SBSConstFloat4,

    Output         as SBSOutput,

    FunctionGraph  as SBSFunctionGraph,
    FunctionNode   as SBSFunctionNode,
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

class ResolveShaderToyIntrinsics(Pass):

    LOOKUP_TABLE = {
        # 'fragCoord'  : '$pos', # TODO for now fragCoord is considered as function parameter -> no need to remap it to $pos
        'iResolution': '$size',
    }

    def visit_Attribute(self, node):
        return IRAttribute(
            variable=self.LOOKUP_TABLE.get(node.variable, node.variable),
            fields=node.fields,
        )

class ResolveGraphStatements(Pass):

    def __init__(self):
        super().__init__()
        self.graph = None

    def visit_FunctionGraph(self, node):

        node_resolvers = SBSFunctionGraphNodeResolvers()
        for statement in node._statements:
            node_resolvers.visit(statement)

        outputs = [
            statement
            for statement in node._statements
            if isinstance(statement, SBSOutput)
        ]

        if len(outputs) > 1:
            raise TranspilerError(f'Found {len(outputs)} outputs for a Function graph, only 0/1 is expected : {pformat([dump(_) for _ in outputs])}')

        return SBSFunctionGraph(
            identifier=node.identifier,
            parameters=node.parameters,
            _statements=node._statements,
            nodes=node_resolvers.nodes,
            outputs=outputs,
        )

class SBSFunctionGraphNodeResolvers(ast.NodeVisitor):
    def __init__(self):
        self.nodes = list()

    def __add(self, node):
        if node not in self.nodes:
            self.nodes.append(node)

    def visit_Set(self, node):
        self.visit(node.from_node)
        self.__add(node)

    def visit_Div(self, node):
        self.visit(node.a)
        self.visit(node.b)
        self.__add(node)

    def visit_Output(self, node):
        self.visit(node.node)

    def visit_GetFloat1(self, node):
        self.__add(node)

    def visit_GetFloat2(self, node):
        self.__add(node)

    def visit_GetFloat3(self, node):
        self.__add(node)

    def visit_GetFloat4(self, node):
        self.__add(node)

    def visit_ConstFloat1(self, node):
        self.__add(node)

    def visit_ConstFloat2(self, node):
        self.__add(node)

    def visit_ConstFloat3(self, node):
        self.__add(node)

    def visit_ConstFloat4(self, node):
        self.__add(node)

    def visit_Swizzle2(self, node):
        self.visit(node.from_node)
        self.__add(node)

    def visit_Swizzle3(self, node):
        self.visit(node.from_node)
        self.__add(node)

    def visit_Swizzle4(self, node):
        self.visit(node.from_node)
        self.__add(node)

    def generic_visit(self, node):
        raise NotImplementedError(dump(node))

DEFAULT_PRE_PASSES = [
    ResolveConstNode,
    ResolveShaderToyIntrinsics,
]

DEFAULT_POST_PASSES = [
    ResolveGraphStatements,
    # ShaderToyIntrinsicPass,
    # ResolveParameterTypeFromDefaultValue,
    # FoldPow2ExpressionPass,
    # ResolveFunctionOverloadSetPass,
    # FlattenOverloadedFunctionsPass,
]
