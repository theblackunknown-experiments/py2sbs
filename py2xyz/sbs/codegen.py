
import io
import ast
import logging

from pathlib import Path

logger = logging.getLogger(__name__)

from py2xyz import (
    dump,
)

from py2xyz.sbs.ast import *

from pysbs.context import Context
from pysbs.sbsenum import (
    WidgetEnum,
)
from pysbs.sbsgenerator import createSBSDocument

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
        logger.debug(f'exc_type, exc_value, traceback : {(exc_type, exc_value, traceback)}')
        if self.sbs:
            logger.debug(f'Substance document is valid, writing it to disk...')
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

        for node_parameter in node.parameters:
            subgenerator.visit(node_parameter)

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

    def __init__(self, graph):
        self.graph = graph

    def visit_Parameter(self, node):
        self.graph.addInputParameter(
            aIdentifier=node.identifier,
            aWidget=self.DEFAULT_WIDGET_FROM_TYPE[node.type],
            # TODO default value
        )
