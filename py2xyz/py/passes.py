
import ast
import logging

logger = logging.getLogger(__name__)

from py2xyz import dump

from py2xyz.py import TranspilerError

class Pass(ast.NodeTransformer):
    pass

class ShaderToyEntryPointInputOutputPass(Pass):

    EXPECTED_ARGUMENT_FRAG_COORD = ('fragCoord', 'vec2')
    EXPECTED_ARGUMENT_FRAG_COLOR = ('fragColor', 'vec4')

    EXPECTED_ARGUMENTS = (
        EXPECTED_ARGUMENT_FRAG_COORD,
        EXPECTED_ARGUMENT_FRAG_COLOR,
    )

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
                raise TranspilerError(f'Expected arguments not found: {self.EXPECTED_ARGUMENTS}\n{dump(node.args)}')

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
    ShaderToyEntryPointInputOutputPass,
]
