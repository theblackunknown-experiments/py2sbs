
import ast
import logging

logger = logging.getLogger(__name__)

from py2xyz import TranspilerError

class Pass(ast.NodeTransformer):
    pass

DEFAULTS = [
]
