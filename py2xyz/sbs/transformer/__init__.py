
import ast
import logging
from itertools import zip_longest

from typing import Union

logger = logging.getLogger(__name__)

from py2xyz import (
    dump,
)

from py2xyz.sbs.ast import (
    Package,
    FunctionGraph,
    Parameter,
)

class UnsupportedASTNode(ValueError):
    pass

class SubstancePackageTranspiler(ast.NodeTransformer):

    def visit_Module(self, node : ast.Module):
        return ast.copy_location(
            Package(
                description=self.__transpile_package_description(node),
                content=list(filter(None, (
                    self.__transpile_package_content(node)
                    for node in ast.iter_child_nodes(node)
                    if isinstance(node, (ast.FunctionDef))
                )))
            ),
            node
        )

    def __transpile_package_description(self, node : ast.Module):
        return next((
            # subnode
            ast.literal_eval(subnode.value)
            for subnode in ast.iter_child_nodes(node)
            if isinstance(subnode, ast.Expr)
            if isinstance(subnode.value, ast.Str)
        ), None)

    def __transpile_package_content(self, node : Union[ast.FunctionDef]):
        if isinstance(node, ast.FunctionDef):
            return self.__transpile_function_graph(node)
        else:
            return None

    def __transpile_function_graph(self, node : ast.FunctionDef):
        return FunctionGraph(
            identifier=node.name,
            parameters=self.__transpile_parameters(node.args),
            nodes=self.__transpile_nodes(node.body),
        )

    def __transpile_parameters(self, node : ast.arguments):
        if node.vararg is not None:
            raise UnsupportedASTNode(f'arguments.varag : {dump(node.vararg)}')

        parameters = [
            Parameter(identifier=subnode.arg, type=self.__transpile_parameter_type(subnode.annotation), value=None)
            for subnode in node.args
        ]

        for parameter, node_default in zip(parameters[-len(node.defaults):], node.defaults):
            parameter.value = node_default
            # TODO make sure node_default is constant expression
            # TODO deduce type from node_default

        return parameters

    def __transpile_parameter_type(self, annotation):
        if isinstance(annotation, ast.Name):
            return annotation.id
        else:
            return None

    def __transpile_nodes(self, *nodes):
        return []
