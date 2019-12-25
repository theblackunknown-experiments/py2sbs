
import ast
import pprint
import logging
import itertools

logger = logging.getLogger(__name__)

from py2xyz import dump

from py2xyz.sbs.ast import *

from py2xyz.sbs.analysis import iterate_inferred_argument_types

class Pass(ast.NodeTransformer):
    pass

class ResolveParameterFromDefaultValue(Pass):

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
                type=ResolveParameterFromDefaultValue.type_from_default(node.value),
                value=node.value,
            )
        else:
            return node

class ResolveFunctionOverloadSetPass(Pass):
    def visit_FunctionGraph(self, node):
        if len(node.parameters) == 0:
            return node

        overloads=list(iterate_inferred_argument_types(node, node.parameters, node.nodes))
        logger.debug(f'overloads : {pprint.pformat(overloads)}')
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
                itertools.chain.from_iterable(map(self.flatten_overloads, node.content) )
            )
        )

DEFAULT_COMPILATION_PASSES = [
    ResolveParameterFromDefaultValue,
    ResolveFunctionOverloadSetPass,
    FlattenOverloadedFunctionsPass,
]
