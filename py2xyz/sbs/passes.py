
import ast
import pprint
import logging
import itertools

logger = logging.getLogger(__name__)

from py2xyz import dump

from py2xyz import TranspilerError

from py2xyz.sbs.ast import *

from py2xyz.sbs.analysis import iterate_inferred_argument_types

class Pass(ast.NodeTransformer):
    pass

class ResolveParameterTypeFromAnnotation(Pass):

    @staticmethod
    def type_from_default(node):
        if isinstance(node, ast.Num):
            return next(
                enum_symbol
                for enum_symbol in itertools.chain(ANY_TYPES)
                if enum_symbol.value == node.n.__class__.__name__
            )
        else:
            logger.warning(f'Unable to resolve type from default value expression: {dump(node)}')
            return None

    def visit_Parameter(self, node):
        if (node.value is not None) and (node.type is None):
            return Parameter(
                identifier=node.identifier,
                type=ResolveParameterTypeFromDefaultValue.type_from_default(node.value),
                value=node.value,
            )
        else:
            return node

class ResolveParameterTypeFromDefaultValue(Pass):

    @staticmethod
    def type_from_default(node):
        if isinstance(node, ast.Num):
            return next(
                enum_symbol
                for enum_symbol in itertools.chain(ANY_TYPES)
                if enum_symbol.value == node.n.__class__.__name__
            )
        else:
            logger.warning(f'Unable to resolve type from default value expression: {dump(node)}')
            return None

    def visit_Parameter(self, node):
        if (node.value is not None) and (node.type is None):
            return Parameter(
                identifier=node.identifier,
                type=ResolveParameterTypeFromDefaultValue.type_from_default(node.value),
                value=node.value,
            )
        else:
            return node

class ResolveFunctionOverloadSetPass(Pass):
    def visit_FunctionGraph(self, node):
        if len(node.parameters) == 0:
            return node

        overloads=list(iterate_inferred_argument_types(node, node.parameters, node.nodes))
        # logger.debug(f'overloads : {pprint.pformat(overloads)}')
        if len(overloads) == 0:
            return node
        elif len(overloads) == 1:
            return FunctionGraph(
                identifier=node.identifier,
                attributes=node.attributes,
                nodes=node.nodes,
                parameters=[
                    Parameter(
                        identifier=parameter.identifier,
                        type=parametertype,
                        value=parameter.value,
                    )
                    for parameter, parametertype in zip(node.parameters, overloads[0])
                ],
            )
        else:
            return OverloadedFunctionGraph(
                identifier=node.identifier,
                attributes=node.attributes,
                parameters=node.parameters,
                nodes=node.nodes,
                overloads=overloads,
            )

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

class FlattenOverloadedFunctionsPass(Pass):
    # Inspired by struct module packing
    FORMAT_CHARACTERS_TABLE = {
        TextTypes.String       :  's',
        LogicalTypes.Boolean   :  'b',
        NumericalTypes.Integer1: 'i1',
        NumericalTypes.Integer2: 'i2',
        NumericalTypes.Integer3: 'i3',
        NumericalTypes.Integer4: 'i4',
        NumericalTypes.Float1  : 'f1',
        NumericalTypes.Float2  : 'f2',
        NumericalTypes.Float3  : 'f3',
        NumericalTypes.Float4  : 'f4',
    }

    @staticmethod
    def packargtypes(argtypes):
        return '-'.join(
            map(
                FlattenOverloadedFunctionsPass.FORMAT_CHARACTERS_TABLE.get,
                argtypes,
            )
        )

    def flatten_overloads(self, node):
        if not isinstance(node, OverloadedFunctionGraph):
            return ( node, )

        return (
            FunctionGraph(
                identifier=f'{node.identifier}_{FlattenOverloadedFunctionsPass.packargtypes(argtypes)}',
                attributes=node.attributes,
                nodes=node.nodes,
                parameters=[
                    Parameter(
                        identifier=parameter.identifier,
                        type=parametertype,
                        value=parameter.value,
                    )
                    for parameter, parametertype in zip(node.parameters, argtypes)
                ],
            )
            for argtypes in node.overloads
        )

    def visit_Package(self, node):
        return Package(
            description=node.description,
            content=list(
                # i.e. flatmap
                itertools.chain.from_iterable(map(self.flatten_overloads, node.content))
            )
        )

class ShaderToyIntrinsicPass(Pass):

    INTRINSIC_LOOKUP_TABLE = {
        'iResolution': '$size',
    }

    def visit_arguments(self, node):
        return ast.arguments(
            args=[
                arg
                for arg in node.args
                if isinstance(arg.annotation, ast.Name)
                if (arg.arg, arg.annotation.id) != self.EXPECTED_ARGUMENT_FRAG_COLOR
            ],
            vararg=node.vararg,
            kwonlyargs=node.kwonlyargs,
            kw_defaults=node.kw_defaults,
            kwarg=node.kwarg,
            # TODO get rid of defaults on 'fragColor'
            defaults=node.defaults,
        )

    def visit_FunctionDef(self, node):
        if node.name == 'mainImage':
            are_arguments_valid = all(
                next((
                    True
                    for arg in node.args.args
                    if isinstance(arg.annotation, ast.Name)
                    if (arg.arg, arg.annotation.id) == expected_arg
                ), False)
                for expected_arg in self.EXPECTED_ARGUMENTS
            )

            if not are_arguments_valid:
                raise TranspilerError(f'Expected arguments not found: {self.EXPECTED_ARGUMENTS}', node.args)

            return ast.FunctionDef(
                name=node.name,
                args=self.visit(node.args),
                body=[
                    ast.Assign(
                        targets=[ ast.Name(id='fragColor', ctx=ast.Store()) ],
                        value=ast.Call(
                            func=ast.Name(id='vec4', ctx=ast.Load()),
                            args=[ ast.Num(n=0.0) ] * 4,
                            keywords=[],
                        )
                    )
                ] + node.body + [
                    ast.Return(
                        value=ast.Name(id='fragColor', ctx=ast.Load())
                    )
                ]
            )
        else:
            return node

DEFAULTS = [
    # ShaderToyIntrinsicPass,
    ResolveParameterTypeFromDefaultValue,
    FoldPow2ExpressionPass,
    ResolveFunctionOverloadSetPass,
    FlattenOverloadedFunctionsPass,
]
