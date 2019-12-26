
import ast
import enum
import logging
import itertools

logger = logging.getLogger(__name__)

from py2xyz import TranspilerError

from py2xyz.ir.ast import (
    Assign             as IRAssign,
    Attribute          as IRAttribute,
    BinaryOperation    as IRBinaryOperation,
    Call               as IRCall,
    Constant           as IRConstant,
    Function           as IRFunction,
    Module             as IRModule,
    OverloadedFunction as IROverloadedFunction,
    Parameter          as IRParameter,
    Reference          as IRReference,
    Return             as IRReturn,
    UnaryOperation     as IRUnaryOperation,
)

from py2xyz.sbs.ast import *

class Transpiler(ast.NodeTransformer):
    def generic_visit(self, node):
        raise TranspilerError(node=node)

class CallOperandsTranspiler(Transpiler):

    def visit_Num(self, node):
        return (
            Constant(value=node.n),
        )

class FunctionBodyExpressionTranspiler(Transpiler):

    def visit_Name(self, node):
        if not isinstance(node.ctx, ast.Load):
            raise TranspilerError(f'Unexpected node encounter during visit', node)
        return IRReference(variable=node.id)

    def visit_Num(self, node):
        return IRConstant(value=node.n)

    def visit_Tuple(self, node):
        count = len(node.elts)
        if count not in {1, 2, 3, 4}:
            raise TranspilerError(f'Tuple count unusupported', node)

        subnodes = list(map(self.visit, node.elts))

        are_subnodes_constants = all(
            isinstance(_, Constant)
            for _ in subnodes
        )
        if not are_subnodes_constants:
            # TODO if not constants, we need to transpile to Vector XYZW or Cast operator
            raise TranspilerError(f'Tuple elements unusupported', node)

        return Constant(value=[_.value for _ in subnodes])

    def visit_BinOp(self, node):
        return IRBinaryOperation(
            left=self.visit(node.left),
            right=self.visit(node.right),
            operator=node.op.__class__.__name__.lower(),
        )

    def visit_Call(self, node):
        assert isinstance(node.func, ast.Name)
        assert isinstance(node.func.ctx, ast.Load)

        if node.keywords:
            raise TranspilerError(f'Call keywords not yet supported', node.keywords)

        operands_transpiler = CallOperandsTranspiler()
        return IRCall(
            function=node.func.id,
            args=list(
                # i.e. flatmap
                itertools.chain.from_iterable(map(operands_transpiler.visit, node.args)),
            ),
            kwargs=list(
                # i.e. flatmap
                itertools.chain.from_iterable(
                    zip(map(operands_transpiler.visit, node.keywords)),
                )
            ),
        )

    def visit_Attribute(self, node):
        assert isinstance(node.ctx, ast.Load)
        assert isinstance(node.value, ast.Name)
        assert isinstance(node.value.ctx, ast.Load)

        return IRAttribute(
            variable=node.value.id,
            fields=node.attr,
        )

class FunctionGraphNodesTranspiler(Transpiler):

    def visit_Return(self, node):
        subtranspiler = FunctionBodyExpressionTranspiler()
        return (
            IRReturn(expression=subtranspiler.visit(node.value)),
        )

    def visit_Assign(self, node):
        # TODO https://en.wikipedia.org/wiki/Static_single_assignment_form
        if len(node.targets) > 1:
            raise TranspilerError(f'Assignements with multiple targets not supported', node)

        target = node.targets[0]
        if not isinstance(target, ast.Name):
            raise TranspilerError(f'Assignement target other than Name not supported', target)

        assert isinstance(target.ctx, ast.Store)

        subtranspiler = FunctionBodyExpressionTranspiler()
        return (
            IRAssign(identifier=target.id, expression=subtranspiler.visit(node.value)),
        )

class FunctionGraphTranspiler(Transpiler):

    def visit_Function(self, node : ast.FunctionDef):
        subtranspiler = FunctionGraphNodesTranspiler()
        return IROverloadedFunction(
            identifier=node.name,
            arguments=node.arguments,
            body=list(
                # i.e. flatmap
                itertools.chain.from_iterable(map(subtranspiler.visit, node.body))
            ),
            overloads=[]
        )

class PackageTranspiler(Transpiler):

    def visit_Module(self, node):
        return IRModule(
            description=node.description,
            content=list(filter(None,(
                self.visit(node)
                for node in node.content
            )))
        )

    def visit_Function(self, node):
        return FunctionGraphTranspiler().visit(node)
