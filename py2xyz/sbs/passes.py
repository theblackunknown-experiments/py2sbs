
import ast
import logging

logger = logging.getLogger(__name__)

from py2xyz import dump

from py2xyz.sbs.ast import *

from py2xyz.sbs.analysis import resolve_overloads

class ResolveFunctionOverloadSetPass(ast.NodeTransformer):
    def visit_FunctionGraph(self, node):
        return OverloadedFunctionGraph(
            identifier=node.identifier,
            attributes=node.attributes,
            parameters=node.parameters,
            nodes=node.nodes,
            overloads=resolve_overloads(node, node.parameters, node.nodes),
        )

DEFAULT_COMPILATION_PASSES = [
    ResolveFunctionOverloadSetPass,
]
