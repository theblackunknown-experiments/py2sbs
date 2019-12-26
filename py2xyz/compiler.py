
import ast
import itertools

from py2xyz import TranspilerError

from py2xyz.ir import (
    Assign          as IRAssign,
    Attribute       as IRAttribute,
    BinaryOperation as IRBinaryOperation,
    Call            as IRCall,
    Constant        as IRConstant,
    Function        as IRFunction,
    Module          as IRModule,
    Parameter       as IRParameter,
    Reference       as IRReference,
    Return          as IRReturn,
    UnaryOperation  as IRUnaryOperation,

    Addition        as IRAddition,
    Substraction    as IRSubstraction,
    Modulo          as IRModulo,
    Multiplication  as IRMultiplication,
    Division        as IRDivision,
    Negation        as IRNegation,
    And             as IRAnd,
    Or              as IROr,
    Not             as IRNot,
    Equals          as IREquals,
)

class Transpiler(ast.NodeTransformer):
    def generic_visit(self, node):
        raise TranspilerError(node=node)

class CallOperandsTranspiler(Transpiler):

    def visit_Num(self, node):
        return (
            IRConstant(value=node.n),
        )

class BinaryOperationOperatorTranspiler(Transpiler):

    def visit_Add(self, node):
        return IRAddition()

    def visit_Sub(self, node):
        return IRSubstraction()

    def visit_Mul(self, node):
        return IRMultiplication()

    def visit_Div(self, node):
        return IRDivision()

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
            operator=BinaryOperationOperatorTranspiler().visit(node.op),
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

class FunctionBodyStatementTranspiler(Transpiler):

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

class FunctionTranspiler(Transpiler):

    def visit_FunctionDef(self, node : ast.FunctionDef):
        subtranspiler = FunctionBodyStatementTranspiler()
        return IRFunction(
            identifier=node.name,
            arguments=self.visit_arguments(node.args),
            body=list(
                # i.e. flatmap
                itertools.chain.from_iterable(map(subtranspiler.visit, node.body))
            ),
        )

    def visit_arguments(self, node : ast.arguments):
        if node.vararg:
            raise TranspilerError(f'varargs arguments not supported', node)

        if node.defaults:
            defaults_count = len(node.defaults)
            return [
                IRParameter(
                    identifier=node_parameter.arg,
                    annotation=node_parameter.annotation.id,
                    expression=None
                )
                for node_parameter in node.args[:-defaults_count]
            ] + [
                IRParameter(
                    identifier=node_parameter.arg,
                    annotation=node_parameter.annotation.id,
                    expression=node_default
                )
                for node_parameter, node_default in zip(node.args[-defaults_count:], node.defaults)
            ]
        else:
            return [
                IRParameter(
                    identifier=node_parameter.arg,
                    annotation=node_parameter.annotation.id,
                    expression=None
                )
                for node_parameter in node.args
            ]

class ModuleTranspiler(Transpiler):

    def visit_Module(self, node):
        node_description = next((
            # subnode
            subnode
            for subnode in ast.iter_child_nodes(node)
            if isinstance(subnode, ast.Expr)
            if isinstance(subnode.value, ast.Str)
        ), None)
        if node_description is not None:
            node.body.remove(node_description)
        return IRModule(
            description=ast.literal_eval(node_description.value) if node_description else None,
            content=list(filter(None,(
                self.visit(node)
                for node in ast.iter_child_nodes(node)
            )))
        )

    def visit_FunctionDef(self, node):
        return FunctionTranspiler().visit(node)

