
"""Python DSL to decribe Substance Graph"""

__version__     = '0.0.0'
__author__      = 'Andréa Machizaud'

import ast

# cf. https://bitbucket.org/takluyver/greentreesnakes/src/default/astpp.py
def dump(node, annotate_fields=True, include_attributes=False, indent='  ', depth=None):
    """
    Return a formatted dump of the tree in *node*.  This is mainly useful for
    debugging purposes.  The returned string will show the names and the values
    for fields.  This makes the code impossible to evaluate, so if evaluation is
    wanted *annotate_fields* must be set to False.  Attributes such as line
    numbers and column offsets are not dumped by default.  If this is wanted,
    *include_attributes* can be set to True.
    """
    def _format(node, _depth, _max_depth=None):
        if (_max_depth is not None) and (_depth > _max_depth):
            return '<...>'

        _next_depth = _depth + 1
        _indent    = indent * (_depth - 1)
        _subindent = indent * _depth
        if isinstance(node, ast.AST):
            formatted_fields = [
                (name, _format(value, _depth=_next_depth, _max_depth=_max_depth))
                for name, value in ast.iter_fields(node)
            ]

            if include_attributes and node._attributes:
                formatted_fields.extend([
                    (
                        attributename,
                        _format(getattr(node, attributename), _depth=_next_depth, _max_depth=_max_depth)
                    )
                    for attributename in node._attributes
                ])


            if annotate_fields:
                return f'{node.__class__.__name__}(' + ', '.join( f'{name}={value}' for name, value in formatted_fields ) + ')'
            else:
                return f'{node.__class__.__name__}({", ".join( fieldname for fieldname, _ in formatted_fields )})'

        elif isinstance(node, list):
            nodes = node

            formatted_nodes = [ '[' ]
            formatted_nodes.extend(
                f'{_subindent}{_format(subnode, _depth=_next_depth, _max_depth=_max_depth)},'
                for subnode in nodes
            )

            if len(formatted_nodes) > 1:
                formatted_nodes.append(f'{_indent}]')
            else:
                formatted_nodes[-1] += ']'
            return '\n'.join(formatted_nodes)

        else:
            return repr(node)

    if not isinstance(node, ast.AST):
        raise TypeError('expected AST, got %r' % node.__class__.__name__)

    return _format(node, _depth=1, _max_depth=depth)

class TranspilerError(RuntimeError):
    def __init__(self, msg=None, node=None):
        if msg and node:
            super().__init__(f'{msg}\n{dump(node, include_attributes=True)}')
        elif msg and not node:
            super().__init__(msg)
        elif not msg and node:
            super().__init__(dump(node, include_attributes=True))
        else:
            super().__init__()

        self.node = node
