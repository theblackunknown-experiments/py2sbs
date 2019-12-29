
import io
import ast
import logging

from pprint import pformat

from pathlib import Path

logger = logging.getLogger(__name__)

from py2xyz import dump, TranspilerError

from py2xyz.sbs.ast import (
    Package            as SBSPackage,
    FunctionGraph      as SBSFunctionGraph,
    FunctionParameter  as SBSFunctionParameter,

    TextTypes          as SBSTextTypes,
    LogicalTypes       as SBSLogicalTypes,
    NumericalTypes     as SBSNumericalTypes,

    Addition           as SBSAddition,
    Substraction       as SBSSubstraction,
    Modulo             as SBSModulo,
    Multiplication     as SBSMultiplication,
    Division           as SBSDivision,
    Negation           as SBSNegation,
    Dot                as SBSDot,
    Cross              as SBSCross,
    Modulus            as SBSModulus,
    Floor              as SBSFloor,
    Ceil               as SBSCeil,
    Cos                as SBSCos,
    Sin                as SBSSin,
    SquareRoot         as SBSSquareRoot,
    NaturalLogarithm   as SBSNaturalLogarithm,
    Logarithm2         as SBSLogarithm2,
    NaturalExponential as SBSNaturalExponential,
    PowerOf2           as SBSPowerOf2,
)

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

class Generator(ast.NodeVisitor):
    def __init__(self):
        self.logger = logging.getLogger(f'{__name__}.{self.__class__.__name__}')

    def generic_visit(self, node):
        raise TranspilerError(node=node)

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

        subgenerator = FunctionGraphGenerator(graph)
        subgenerator.visit(node)

class FunctionGraphGenerator(Generator):

    def __init__(self, graph):
        super().__init__()
        self.graph = graph

    def visit_FunctionGraph(self, node):
        symboltable = { }

        subgenerator_parameters = FunctionGraphParametersGenerator(self.graph, symboltable)
        for subnode in node.parameters:
            subgenerator_parameters.visit(subnode)

        self.logger.debug(f'symtable after parameters: {pformat(symboltable)}')

        subgenerator_nodes = FunctionGraphNodesGenerator(self.graph, symboltable)
        for subnode in node.nodes:
            subgenerator_nodes.visit(subnode)

        self.logger.debug(f'symtable after nodes: {pformat(symboltable)}')

        for sbsnode in ( symboltable[_.node] for _ in node.outputs ):
            self.graph.setOutputNode(sbsnode)

class FunctionGraphParametersGenerator(Generator):

    DEFAULT_WIDGET_FROM_TYPE = {
        SBSNumericalTypes.Integer1: WidgetEnum.SLIDER_INT1,
        SBSNumericalTypes.Integer2: WidgetEnum.SLIDER_INT2,
        SBSNumericalTypes.Integer3: WidgetEnum.SLIDER_INT3,
        SBSNumericalTypes.Integer4: WidgetEnum.SLIDER_INT4,
        SBSNumericalTypes.Float1  : WidgetEnum.SLIDER_FLOAT1,
        SBSNumericalTypes.Float2  : WidgetEnum.SLIDER_FLOAT2,
        SBSNumericalTypes.Float3  : WidgetEnum.SLIDER_FLOAT3,
        SBSNumericalTypes.Float4  : WidgetEnum.SLIDER_FLOAT4,
    }

    def __init__(self, graph, symboltable):
        super().__init__()
        self.graph = graph
        self.symboltable = symboltable

    def visit_FunctionParameter(self, node):
        sbsparameter = self.graph.addInputParameter(
            aIdentifier=node.identifier,
            aWidget=self.DEFAULT_WIDGET_FROM_TYPE[node.type],
            # TODO default value
        )
        self.symboltable.update({
            node.identifier: sbsparameter
        })
        self.logger.debug(f'{dump(node, depth=2)} -> {sbsparameter}')
        return sbsparameter

class FunctionGraphNodesGenerator(Generator):

    TYPE_TO_FUNCTION = {
        SBSLogicalTypes.Boolean   : FunctionEnum.GET_BOOL,
        SBSNumericalTypes.Integer1: FunctionEnum.GET_INTEGER1 ,
        SBSNumericalTypes.Integer2: FunctionEnum.GET_INTEGER2 ,
        SBSNumericalTypes.Integer3: FunctionEnum.GET_INTEGER3 ,
        SBSNumericalTypes.Integer4: FunctionEnum.GET_INTEGER4 ,
        SBSNumericalTypes.Float1  : FunctionEnum.GET_FLOAT1   ,
        SBSNumericalTypes.Float2  : FunctionEnum.GET_FLOAT2   ,
        SBSNumericalTypes.Float3  : FunctionEnum.GET_FLOAT3   ,
        SBSNumericalTypes.Float4  : FunctionEnum.GET_FLOAT4   ,
        SBSTextTypes.String       : FunctionEnum.GET_STRING   ,
    }

    OPCODE_TO_FUNCTION = {
        SBSAddition       : FunctionEnum.ADD,
        SBSSubstraction   : FunctionEnum.SUB,
        SBSMultiplication : FunctionEnum.MUL,
        SBSDivision       : FunctionEnum.DIV,
        SBSModulo         : FunctionEnum.MOD,
        SBSPowerOf2       : FunctionEnum.POW2,
    }

    def __init__(self, graph, symboltable):
        super().__init__()
        self.graph = graph
        self.symboltable = symboltable

    def visit_GetFloat2(self, node):
        sbsnode = self.graph.createFunctionNode(
            aFunction=FunctionEnum.GET_FLOAT2,
            aParameters={
                FunctionEnum.GET_FLOAT2: node.variable
            }
        )
        self.logger.debug(f'{dump(node, depth=1)} -> {sbsnode}')
        self.symboltable[node] = sbsnode
        return sbsnode

    def visit_ConstFloat4(self, node):
        sbsnode = self.graph.createFunctionNode(
            aFunction=FunctionEnum.CONST_FLOAT4,
            aParameters={
                FunctionEnum.CONST_FLOAT4: [node.x, node.y, node.z, node.w]
            }
        )
        self.logger.debug(f'{dump(node, depth=1)} -> {sbsnode}')
        self.symboltable[node] = sbsnode
        return sbsnode

    def visit_Set(self, node):
        lnode = self.symboltable[node.from_node]
        sbsnode = self.graph.createFunctionNode(
            aFunction=FunctionEnum.SET,
            aParameters={
                FunctionEnum.SET: node.value
            }
        )
        self.graph.connectNodes(lnode, sbsnode)
        self.logger.debug(f'{dump(node, depth=1)} -> {sbsnode}')
        self.symboltable[node] = sbsnode
        return sbsnode

    def visit_Swizzle2(self, node):
        lnode = self.symboltable[node.from_node]
        sbsnode = self.graph.createFunctionNode(
            aFunction=FunctionEnum.SWIZZLE2,
            aParameters={
                FunctionEnum.SWIZZLE2: [
                    node._0,
                    node._1,
                ]
            }
        )
        self.graph.connectNodes(lnode, sbsnode, FunctionInputEnum.VECTOR)
        self.logger.debug(f'{dump(node, depth=1)} -> {sbsnode}')
        self.symboltable[node] = sbsnode
        return sbsnode

    def visit_Div(self, node):
        anode = self.symboltable[node.a]
        bnode = self.symboltable[node.b]

        sbsnode = self.graph.createFunctionNode(FunctionEnum.DIV)

        self.graph.connectNodes(anode, sbsnode, FunctionInputEnum.A)
        self.graph.connectNodes(bnode, sbsnode, FunctionInputEnum.B)

        self.logger.debug(f'{dump(node, depth=1)} -> {sbsnode}')
        self.symboltable[node] = sbsnode
        return sbsnode
