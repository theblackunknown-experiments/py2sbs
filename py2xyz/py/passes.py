
import ast
import logging

logger = logging.getLogger(__name__)

from py2xyz import TranspilerError

class Pass(ast.NodeTransformer):
    pass

DEFAULT_PRE_PASSES = [
]

DEFAULT_POST_PASSES = [
]
