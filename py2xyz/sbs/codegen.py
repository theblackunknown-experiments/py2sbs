
import io
import ast
import logging

from pathlib import Path

logger = logging.getLogger(__name__)

from py2xyz import (
    dump,
)

from py2xyz.sbs.ast import *

from py2xyz.sbs.symtable import FunctionSymbolTable

from pysbs.context import Context
from pysbs.sbsenum import (
    WidgetEnum,
    ParamTypeEnum,
    FunctionEnum,
    FunctionInputEnum,
)
from pysbs.sbsgenerator import createSBSDocument
from pysbs.autograph.ag_layout import layoutDoc as layout

class UnsupportedASTNode(RuntimeError):
    pass

class Generator(ast.NodeVisitor):
    def generic_visit(self, node):
        raise UnsupportedASTNode(dump(node))

class PackageGenerator(Generator):
    def __init__(self, stream : io.FileIO):
        assert isinstance(stream, (io.FileIO, io.TextIOWrapper))

        # NOTE pysbs requires a filepath
        stream.close()
        self.path = stream.name
        self.sbs = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is not None:
            raise

        if self.sbs:
            logger.info(f'Laying out Substance document graphs...')
            layout(self.sbs)

            logger.info(f'Substance document is valid, writing it to disk...')
            self.sbs.writeDoc()
        else:
            logger.debug(f'Substance document is invalid, aborting write to disk')

    def visit_Package(self, node):
        sbs = createSBSDocument(Context(), self.path)
        if node.description:
            sbs.setDescription(node.description)

        self.sbs = sbs
        logger.debug(f'Substance document created from {dump(node)}')

        for subnode in node.content:
            self.visit(subnode)

    def visit_FunctionGraph(self, node):
        graph = self.sbs.createFunction(
            aFunctionIdentifier=node.identifier,
        )

        subgenerator = GraphGenerator(graph)
        subgenerator.visit(node)

class GraphGenerator(Generator):

    DEFAULT_WIDGET_FROM_TYPE = {
        NumericalTypes.Integer1: WidgetEnum.SLIDER_INT1,
        NumericalTypes.Integer2: WidgetEnum.SLIDER_INT2,
        NumericalTypes.Integer3: WidgetEnum.SLIDER_INT3,
        NumericalTypes.Integer4: WidgetEnum.SLIDER_INT4,
        NumericalTypes.Float1  : WidgetEnum.SLIDER_FLOAT1,
        NumericalTypes.Float2  : WidgetEnum.SLIDER_FLOAT2,
        NumericalTypes.Float3  : WidgetEnum.SLIDER_FLOAT3,
        NumericalTypes.Float4  : WidgetEnum.SLIDER_FLOAT4,
    }

    TYPE_TO_FUNCTION = {
        LogicalTypes.Boolean   : FunctionEnum.GET_BOOL,
        NumericalTypes.Integer1: FunctionEnum.GET_INTEGER1 ,
        NumericalTypes.Integer2: FunctionEnum.GET_INTEGER2 ,
        NumericalTypes.Integer3: FunctionEnum.GET_INTEGER3 ,
        NumericalTypes.Integer4: FunctionEnum.GET_INTEGER4 ,
        NumericalTypes.Float1  : FunctionEnum.GET_FLOAT1   ,
        NumericalTypes.Float2  : FunctionEnum.GET_FLOAT2   ,
        NumericalTypes.Float3  : FunctionEnum.GET_FLOAT3   ,
        NumericalTypes.Float4  : FunctionEnum.GET_FLOAT4   ,
        TextTypes.String       : FunctionEnum.GET_STRING   ,
    }

    OPCODE_TO_FUNCTION = {
        NativeBinaryOperator.Add  : FunctionEnum.ADD,
        NativeBinaryOperator.Sub  : FunctionEnum.SUB,
        NativeBinaryOperator.Mult : FunctionEnum.MUL,
        NativeBinaryOperator.Div  : FunctionEnum.DIV,
        NativeBinaryOperator.Mod  : FunctionEnum.MOD,
        NativeUnaryOperator.Pow2  : FunctionEnum.POW2,
    }

    def __init__(self, graph):
        self.graph = graph
        self.logger = logging.getLogger(f'{__name__}.{self.__class__.__name__}')

    def visit_FunctionGraph(self, node):
        self.symbol_table = FunctionSymbolTable(node.identifier)
        self.logger.debug(f'{node} - generated function symbol table')

        for subnode in ast.iter_child_nodes(node):
            self.visit(subnode)

    def visit_Parameter(self, node):
        sbsparameter = self.graph.addInputParameter(
            aIdentifier=node.identifier,
            aWidget=self.DEFAULT_WIDGET_FROM_TYPE[node.type],
            # TODO default value
        )
        self.symbol_table.update({
            node.identifier: node
        })
        self.logger.debug(f'{node} - generated sbsparameter {sbsparameter}')
        return sbsparameter

    def visit_Output(self, node):
        sbsnode = self.visit(node.expression)
        self.graph.setOutputNode(sbsnode)
        self.logger.debug(f'{node} - generated output node {sbsnode}')
        return sbsnode

    def visit_UnaryOperation(self, node):
        operand_node = self.visit(node.operand)
        operator_node = self.visit(node.operator)

        self.graph.connectNodes(operand_node, operator_node, aRightNodeInput=FunctionInputEnum.A)

        self.logger.debug(f'{node} - connected operator to its input')
        return operator_node

    def visit_BinaryOperation(self, node):
        left_node = self.visit(node.left)
        right_node = self.visit(node.right)
        operator_node = self.visit(node.operator)

        self.graph.connectNodes(left_node, operator_node, aRightNodeInput=FunctionInputEnum.A)
        self.graph.connectNodes(right_node, operator_node, aRightNodeInput=FunctionInputEnum.B)

        self.logger.debug(f'{node} - connected operator to its inputs')
        return operator_node

    def visit_Get(self, node):
        parameter = self.symbol_table.lookup(node.symbol)
        sbsfunction = self.TYPE_TO_FUNCTION[parameter.type]
        sbsnode = self.graph.createFunctionNode(
            aFunction=sbsfunction,
            aParameters={
                sbsfunction: node.symbol
            }
        )
        self.logger.debug(f'{node} - generated get node {sbsnode}')
        return sbsnode

    def visit_Operator(self, node):
        sbsfunction = self.OPCODE_TO_FUNCTION[node.opcode]
        sbsnode = self.graph.createFunctionNode(sbsfunction)
        self.logger.debug(f'{node} - generated operator node {sbsnode}')
        return sbsnode
