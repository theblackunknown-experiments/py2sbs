#!/usr/bin/env python3

import ast
import logging
import logging.config
import argparse
import tempfile
import traceback

from pathlib import Path

logger = logging.getLogger(__name__)

from py2xyz import (
    __name__ as modulename,
    __version__ as moduleversion,
    __doc__ as moduledoc,
    dump,
)

from py2xyz.sbs.transformer import (
    UnsupportedASTNode as SubstanceTransformerUnsupportedASTNode,
    PackageTranspiler as SubstancePackageTranspiler,
)

from py2xyz.sbs.passes import DEFAULT_COMPILATION_PASSES

from py2xyz.sbs.codegen import (
    UnsupportedASTNode as SubstanceCodegenUnsupportedASTNode,
    PackageGenerator as SubstancePackageGenerator,
)

SETTINGS_FOLDER = Path.home() / f'.{modulename}' / moduleversion

def main():
    parser = argparse.ArgumentParser(description=moduledoc)
    parser.add_argument(
        'source_file',
        type=argparse.FileType('rt', encoding='utf-8'),
        help='source filepath to process (supported extensions: .py)',
    )

    parser.add_argument(
        '-t', '--target',
        choices=[
            'sbs',
        ],
        help='target language',
    )

    parser.add_argument(
        '-o', '--output',
        type=argparse.FileType(mode='wt', encoding='utf-8'),
        help='Where to write to generated code',
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

    arguments = parser.parse_args()
    logger.debug(f'Arguments: {arguments}')

    if arguments.source_file is None:
        logger.error(f'missing <source_file>')
        return 1

    if arguments.verbose >= 2:
        logger.setLevel( logging.DEBUG )
    elif arguments.verbose >= 1:
        logger.setLevel( logging.INFO )

    try:
        ast_source_root_node = ast.parse(
            source=arguments.source_file.read(),
            filename=getattr(arguments.source_file, 'name', '<string>'),
        )

        if arguments.pretty_print:
            print(dump(ast_source_root_node))
            return 0

        if arguments.target == 'sbs':

            logger.info(f'Transpilationg from Python to Substance')
            logger.info(f'Input: {dump(ast_source_root_node)}')

            transformer = SubstancePackageTranspiler()
            ast_target_root_node = transformer.visit(ast_source_root_node)

            logger.info(f'Output: {dump(ast_target_root_node)}')

            for idx, CompilationPassClazz in enumerate(DEFAULT_COMPILATION_PASSES, 1):
                compilation_pass = CompilationPassClazz()
                ast_target_root_node = compilation_pass.visit(ast_target_root_node)
                logger.info(f'Optimization {idx} - {CompilationPassClazz.__name__} : {dump(ast_target_root_node)}')

            if arguments.output:
                logger.info(f'Codegen to {arguments.output}')
                with SubstancePackageGenerator(arguments.output) as codegen:
                    codegen.visit(ast_target_root_node)

        return 0
    except (SubstanceTransformerUnsupportedASTNode):
        logger.error(f'Unable to transpile to Substance : {traceback.format_exc()}')
        return -1
    except (SubstanceCodegenUnsupportedASTNode):
        logger.error(f'Unable to codegen to Substance : {traceback.format_exc()}')
        return -1
    except (ValueError, SyntaxError):
        logger.error(f'Invalid DSL : {traceback.format_exc()}')
        return -1

if __name__ == '__main__':

    logging.config.dictConfig({
        'version': 1,
        'formatters': {
            'debug': {
                'format' : '[{filename}:{lineno: >3}] {message}',
                'datefmt': None,
                'style'  : '{',
            },
            'brief': {
                'format' : '[{name}] {message}',
                'datefmt': None,
                'style'  : '{',
            },
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'brief',
                'stream': 'ext://sys.stdout',
            },
            'console_debug': {
                'class': 'logging.StreamHandler',
                'formatter': 'debug',
                'stream': 'ext://sys.stdout',
            },
            'file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'formatter': 'debug',
                'filename': Path('scanbox.log'),
                'maxBytes': 1024*1024*1024*1024,
                'backupCount': 5,
                'encoding': 'utf-8',
            },
            'null': {
                'class': 'logging.NullHandler',
            }
        },
        'loggers': {
            '__main__': {
                'level': 'INFO',
                'handlers': [
                    'console',
                ],
            },
            'py2xyz': {
                'level': 'DEBUG',
                'handlers': [
                    'console_debug',
                ],
            },
            'py2xyz.sbs.analysis': {
                'level': 'DEBUG',
                'handlers': [
                    'null',
                ],
                'propagate': False
            },
        },
    })

    import sys
    sys.exit(main())
