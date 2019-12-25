
import ast
import logging
import itertools

logger = logging.getLogger(__name__)

from py2xyz import (
    dump,
)

from py2xyz.sbs.ast import *

class UnsupportedASTNode(RuntimeError):
    pass

class UnsupportedTranspilerProcessing(RuntimeError):
    pass

class Transpiler(ast.NodeTransformer):
    def generic_visit(self, node):
        raise UnsupportedASTNode(dump(node))

class FunctionGraphNodesTranspiler(Transpiler):

    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Load):
            # TODO use a compilation pass to transform get into reference
            # return Reference(to=self.symbol_table.lookup(node.id))
            return Get(symbol=node.id)
        else:
            raise UnsupportedTranspilerProcessing(f'Unexpected node encounter during visit {dump(node)}')

    def visit_Num(self, node):
        return Constant(value=node.n)

    def visit_Add(self, node):
        return NumericalOperator.Add

    def visit_Mod(self, node):
        return NumericalOperator.Mod

    def visit_Pow(self, node):
        return NumericalOperator.Pow

    def visit_Tuple(self, node):
        count = len(node.elts)
        if count not in {1, 2, 3, 4}:
            raise UnsupportedASTNode(f'Tuple count unusupported : {dump(node)}')

        subnodes = list(map(self.visit, node.elts))

        are_subnodes_constants = all(
            isinstance(_, Constant)
            for _ in subnodes
        )
        if are_subnodes_constants:
            return Constant(value=[_.value for _ in subnodes])
        else:
            # TODO if not constants, we need to transpile to Vector XYZW or Cast operator
            raise UnsupportedASTNode(f'Tuple elements unusupported : {dump(node)}')

    def visit_BinOp(self, node):
        return BinaryOperation(
            left=self.visit(node.left),
            right=self.visit(node.right),
            operator=self.visit(node.op),
        )

    def visit_Return(self, node):
        return Output(expression=self.visit(node.value))

class FunctionGraphTranspiler(Transpiler):

    def __init__(self):
        self.body_transpiler = None

    def visit_FunctionDef(self, node : ast.FunctionDef):
        assert self.body_transpiler is None
        self.body_transpiler = FunctionGraphNodesTranspiler()
        return FunctionGraph(
            identifier=node.name,
            attributes=None,
            parameters=self.visit_arguments(node.args),
            nodes=self.visit_body(node.body),
            overloads=set(),
        )

    def visit_arguments(self, node : ast.arguments):
        if node.vararg is not None:
            raise UnsupportedASTNode(f'arguments.varag : {dump(node.vararg)}')

        def type_from_annotation(annotation):
            if isinstance(annotation, ast.Name):
                return next(
                    enum_symbol
                    for enum_symbol in itertools.chain(ANY_TYPES)
                    if enum_symbol.value == annotation.id
                )
            else:
                return None

        def type_from_default(node):
            if isinstance(node, ast.Num):
                return next(
                    enum_symbol
                    for enum_symbol in itertools.chain(ANY_TYPES)
                    if enum_symbol.value == node.n.__class__.__name__
                )
            else:
                return None

        parameters = [
            Parameter(identifier=subnode.arg, type=type_from_annotation(subnode.annotation), value=None)
            for subnode in node.args
        ]

        for parameter, node_default in zip(parameters[-len(node.defaults):], node.defaults):
            parameter.value = node_default
            if (node_default is not None) and (parameter.type is None):
                parameter.type = type_from_default(node_default)

            # TODO make sure node_default is constant expression
            # TODO deduce type from node_default

        return parameters

    def visit_body(self, nodes):
        return list(filter(None, map(self.body_transpiler.visit, nodes)))

class PackageTranspiler(Transpiler):

    def visit_Module(self, node : ast.Module):
        node_package_description = next((
            # subnode
            subnode
            for subnode in ast.iter_child_nodes(node)
            if isinstance(subnode, ast.Expr)
            if isinstance(subnode.value, ast.Str)
        ), None)
        if node_package_description is not None:
            node.body.remove(node_package_description)
        return Package(
            description=ast.literal_eval(node_package_description.value) if node_package_description else None,
            content=list(filter(None,(
                self.visit(node)
                for node in ast.iter_child_nodes(node)
            )))
        )

    def visit_FunctionDef(self, node : ast.Module):
        return FunctionGraphTranspiler().visit(node)
