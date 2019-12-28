
import ast
import logging
import itertools

from pprint import pformat

logger = logging.getLogger(__name__)

from py2xyz import dump, TranspilerError

from py2xyz.ir.ast import (
    Constant          as IRConstant,
    Reference         as IRReference,
)

from py2xyz.sbs.ast import (
    TextTypes         as SBSTextTypes,
    LogicalTypes      as SBSLogicalTypes,
    NumericalTypes    as SBSNumericalTypes,

    Package           as SBSPackage,
    FunctionGraph     as SBSFunctionGraph,
    FunctionParameter as SBSFunctionParameter,

    Output            as SBSOutput,

    Set               as SBSSet,
    Div               as SBSDiv,
    GetFloat1         as SBSGetFloat1,
    GetFloat2         as SBSGetFloat2,
    GetFloat3         as SBSGetFloat3,
    GetFloat4         as SBSGetFloat4,
    Swizzle2          as SBSSwizzle2,
    Swizzle3          as SBSSwizzle3,
    Swizzle4          as SBSSwizzle4,
)

_DEBUG_DEPTH = 2

class Transpiler(ast.NodeTransformer):
    def __init__(self):
        self.logger = logging.getLogger(f'{__name__}.{self.__class__.__name__}')

    def generic_visit(self, node):
        raise TranspilerError(node=node)

class PackageTranspiler(Transpiler):

    def visit_Module(self, node):
        return SBSPackage(
            description=node.description,
            content=list(filter(None, (
                self.visit(node)
                for node in node.content
            ))),
        )

    def visit_Function(self, node):
        return FunctionGraphTranspiler().visit(node)

class FunctionGraphTranspiler(Transpiler):

    def visit_Function(self, node):
        parameter_transpiler = FunctionGraphParametersTranspiler()
        sbsparameters = list(map(parameter_transpiler.visit, node.arguments))

        node_transpiler = FunctionGraphNodesTranspiler(sbsparameters)

        sbsnode = SBSFunctionGraph(
            identifier=node.identifier,
            parameters=sbsparameters,
            _statements=list(
                itertools.chain.from_iterable(
                    map(
                        node_transpiler.visit,
                        node.body,
                    ),
                )
            )
        )
        self.logger.debug(f'{node.__class__.__name__} -> {dump(sbsnode)}')
        return sbsnode

class FunctionGraphParametersTranspiler(Transpiler):

    def visit_TypedParameter(self, node):

        # TODO Make sure constant expression is valid for sbs
        if node.expression:
            if not isinstance(node.expression, IRConstant):
                raise TranspilerError(f'Non constant parameter value are not supported', node.expression)

        return SBSFunctionParameter(
            identifier=node.identifier,
            type=node.type,
            value=node.expression,
        )

class FunctionGraphNodesTranspiler(Transpiler):

    def __init__(self, sbsparameters):
        super().__init__()
        self.symboltable = { }
        self.symboltable.update({
            parameter.identifier: parameter
            for parameter in sbsparameters
        })

        # sbs intrinsics
        self.symboltable.update({
            '$uv': SBSGetFloat2('$uv'),
            '$size': SBSGetFloat2('$size'),
        })
        self.logger.debug(f'initial symtable {pformat({ (k, dump(v)) for k,v in self.symboltable.items()})}')

    def generic_visit(self, node):
        raise NotImplementedError(dump(node))

    # SBS nodes

    def visit_GetFloat1(self, node):
        return node

    def visit_GetFloat2(self, node):
        return node

    def visit_GetFloat3(self, node):
        return node

    def visit_GetFloat4(self, node):
        return node

    def visit_ConstFloat4(self, node):
        return node

    def visit_FunctionParameter(self, node):
        TYPE_TO_CLASS = {
            SBSNumericalTypes.Float1: SBSGetFloat1,
            SBSNumericalTypes.Float2: SBSGetFloat2,
            SBSNumericalTypes.Float3: SBSGetFloat3,
            SBSNumericalTypes.Float4: SBSGetFloat4,
        }
        return TYPE_TO_CLASS[node.type](variable=node.identifier)

    # IR nodes - Statements

    def visit_Return(self, node):
        if isinstance(node.expression, IRReference):
            if node.expression.variable not in self.symboltable:
                raise TranspilerError(f'{node.expression.variable} variable not bound', node)

            sbsnode = SBSOutput(
                node=self.symboltable[node.expression.variable]
            )
            self.logger.debug(f'{dump(node, depth=_DEBUG_DEPTH)} -> {dump(sbsnode)}')
            return (sbsnode, )
        else:
            raise NotImplementedError(dump(node))

    def visit_Assign(self, node):
        sbsnode = SBSSet(
            value=node.identifier,
            from_node=self.visit(node.expression),
        )
        self.logger.debug(f'{dump(node, depth=_DEBUG_DEPTH)} -> {dump(sbsnode)}')

        self.symboltable[node.identifier] = sbsnode
        self.logger.debug(f'{dump(node, depth=_DEBUG_DEPTH)} symtable update {pformat({ (k, dump(v)) for k,v in self.symboltable.items()})}')
        return (sbsnode, )

    # IR nodes - Expressions

    def visit_BinaryOperation(self, node):
        sbsnode = self.visit(node.operator)
        sbsnode.a = self.visit(node.left)
        sbsnode.b = self.visit(node.right)
        self.logger.debug(f'{dump(node, depth=_DEBUG_DEPTH)} -> {dump(sbsnode)}')
        return sbsnode

    def visit_Division(self, node):
        sbsnode = SBSDiv()
        self.logger.debug(f'{dump(node, depth=_DEBUG_DEPTH)} transpiling to {dump(sbsnode)}')
        return sbsnode

    SWIZZLE_FIELDS_XYZW = 'xyzw'
    SWIZZLE_FIELDS_RGBA = 'rgba'

    SWIZZLE_LOOKUP_XYZW = {
        **{
            tuple(combination) : SBSSwizzle2
            for combination in itertools.combinations_with_replacement(SWIZZLE_FIELDS_XYZW, 2)
        },
        **{
            tuple(combination) : SBSSwizzle3
            for combination in itertools.combinations_with_replacement(SWIZZLE_FIELDS_XYZW, 3)
        },
        **{
            tuple(combination) : SBSSwizzle4
            for combination in itertools.combinations_with_replacement(SWIZZLE_FIELDS_XYZW, 4)
        }
    }

    SWIZZLE_LOOKUP_RGBA = {
        **{
            tuple(combination) : SBSSwizzle2
            for combination in itertools.combinations_with_replacement(SWIZZLE_FIELDS_RGBA, 2)
        },
        **{
            tuple(combination) : SBSSwizzle3
            for combination in itertools.combinations_with_replacement(SWIZZLE_FIELDS_RGBA, 3)
        },
        **{
            tuple(combination) : SBSSwizzle4
            for combination in itertools.combinations_with_replacement(SWIZZLE_FIELDS_RGBA, 4)
        }
    }

    def visit_Attribute(self, node):
        if node.variable not in self.symboltable:
            raise TranspilerError(f'{node.variable} variable not bound', node)

        sbsnodevariable = self.visit(self.symboltable[node.variable])

        # TODO preprocess GLSL swizzle at IR level
        fields_as_tuple = tuple(node.fields)
        if fields_as_tuple in self.SWIZZLE_LOOKUP_XYZW:
            SBSSwizzleClass = self.SWIZZLE_LOOKUP_XYZW[fields_as_tuple]
            Indexer = self.SWIZZLE_FIELDS_XYZW
        elif fields_as_tuple in self.SWIZZLE_LOOKUP_RGBA:
            SBSSwizzleClass = self.SWIZZLE_LOOKUP_RGBA[fields_as_tuple]
            Indexer = self.SWIZZLE_FIELDS_RGBA
        else:
            raise TranspilerError(f'{node.fields} unknown attribute fields for {dump(sbsnodevariable)}', node)

        sbsnode = SBSSwizzleClass(from_node=sbsnodevariable, **{
            f'_{idx}': Indexer.index(fieldname)
            for idx, fieldname in enumerate(node.fields)
        })
        self.logger.debug(f'{dump(node, depth=_DEBUG_DEPTH)} transpiling to {dump(sbsnode)}')
        return sbsnode
