#!/usr/bin/env python3

import ast
import logging
import argparse

from pathlib import Path

logger = logging.getLogger(__name__)

from py2sbs import (
    __version__ as py2sbsversion,
    __doc__ as py2sbsdoc,
)

SETTINGS_FOLDER = Path.home() / '.py2sbs' / py2sbsversion

# cf. https://bitbucket.org/takluyver/greentreesnakes/src/default/astpp.py
def dump(node, annotate_fields=True, include_attributes=False, indent='  '):
    """
    Return a formatted dump of the tree in *node*.  This is mainly useful for
    debugging purposes.  The returned string will show the names and the values
    for fields.  This makes the code impossible to evaluate, so if evaluation is
    wanted *annotate_fields* must be set to False.  Attributes such as line
    numbers and column offsets are not dumped by default.  If this is wanted,
    *include_attributes* can be set to True.
    """
    def _format(node, level=0):
        if isinstance(node, ast.AST):
            fields = [(a, _format(b, level)) for a, b in ast.iter_fields(node)]
            if include_attributes and node._attributes:
                fields.extend([(a, _format(getattr(node, a), level))
                               for a in node._attributes])
            return ''.join([
                node.__class__.__name__,
                '(',
                ', '.join(('%s=%s' % field for field in fields)
                           if annotate_fields else
                           (b for a, b in fields)),
                ')'])
        elif isinstance(node, list):
            lines = ['[']
            lines.extend((indent * (level + 2) + _format(x, level + 2) + ','
                         for x in node))
            if len(lines) > 1:
                lines.append(indent * (level + 1) + ']')
            else:
                lines[-1] += ']'
            return '\n'.join(lines)
        return repr(node)

    if not isinstance(node, ast.AST):
        raise TypeError('expected AST, got %r' % node.__class__.__name__)
    return _format(node)

def main():
    parser = argparse.ArgumentParser(description=py2sbsdoc)
    parser.add_argument(
        'source_file',
        type=argparse.FileType('rt', encoding='utf-8'),
        help='source filepath to process (supported extensions: .py)',
    )

    parser.add_argument(
        '-v', '--verbose',
        help='Make runtime more verbose, more "v", more fun',
        action='count',
        default=0,
    )

    parser.add_argument(
        '--pretty-print',
        help='Print source AST instead of transpiling',
        action='store_true',
    )

    arguments = parser.parse_args( )

    if arguments.source_file is None:
        logger.error(f'missing <source_file>')
        return 1

    if arguments.verbose >= 1:
        logger.setLevel( logging.DEBUG )

    try:
        ast_root_node = ast.parse(
            source=arguments.source_file.read(),
            filename=getattr(arguments.source_file, 'name', '<string>'),
        )

        if arguments.pretty_print:
            logger.info(dump(ast_root_node))
            return 0

        return 0
    except (ValueError, SyntaxError) as e:
        logger.error(f'Invalid DSL : {e}')
        return -1

if __name__ == '__main__':

    logging.basicConfig(
        level=logging.DEBUG,
        format='[{name}] {message}',
        datefmt=None,
        style='{'
    )

    import sys
    sys.exit(main())
