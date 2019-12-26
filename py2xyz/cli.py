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

from py2xyz import TranspilerError

from py2xyz.compiler import ModuleTranspiler as IRModuleTranspiler

from py2xyz.sbs.compiler import (
    PackageTranspiler as SubstancePackageTranspiler,
)

from py2xyz.passes import DEFAULTS as DEFAULT_IR_PASSES
from py2xyz.py.passes import DEFAULTS as DEFAULT_PY_PASSES
from py2xyz.sbs.passes import DEFAULTS as DEFAULT_SBS_PASSES

from py2xyz.sbs.codegen import (
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
        '-p', '--pass',
        dest='passes',
        help='Which Substance pass to run, run all default passes if none provided',
        action='append',
    )

    arguments = parser.parse_args()
    logger.debug(f'Arguments: {arguments}')

    if arguments.source_file is None:
        logger.error(f'missing <source_file>')
        return 1

    if arguments.passes:
        def __filter_pass(pass_clazz):
            return pass_clazz.__name__ in arguments.passes
    else:
        __filter_pass = None

    try:
        ast_source = ast.parse(
            source=arguments.source_file.read(),
            filename=getattr(arguments.source_file, 'name', '<string>'),
        )
        logger.debug(f'source\n{dump(ast_source)}')

        for idx, CompilationPassClazz in enumerate(filter(__filter_pass, DEFAULT_PY_PASSES), 1):
            compilation_pass = CompilationPassClazz()
            ast_source = compilation_pass.visit(ast_source)
            logger.info(f'optimization {idx} - {CompilationPassClazz.__name__}\n{dump(ast_source)}')

        transformer = IRModuleTranspiler()
        ast_ir = transformer.visit(ast_source)

        logger.info(f'IR\n{dump(ast_ir)}')

        for idx, CompilationPassClazz in enumerate(filter(__filter_pass, DEFAULT_IR_PASSES), 1):
            compilation_pass = CompilationPassClazz()
            ast_ir = compilation_pass.visit(ast_ir)
            logger.info(f'optimization {idx} - {CompilationPassClazz.__name__}\n{dump(ast_ir)}')

        if arguments.target == 'sbs':
            logger.info(f'py -> sbs')

            try:
                transformer = SubstancePackageTranspiler()
                ast_sbs = transformer.visit(ast_ir)

                logger.info(f'SBS IR\n{dump(ast_sbs)}')

                for idx, CompilationPassClazz in enumerate(filter(__filter_pass, DEFAULT_SBS_PASSES), 1):
                    compilation_pass = CompilationPassClazz()
                    ast_sbs = compilation_pass.visit(ast_sbs)
                    logger.info(f'optimization {idx} - {CompilationPassClazz.__name__}\n{dump(ast_sbs)}')

                if arguments.output:
                    logger.info(f'codegen -> {arguments.output}')
                    with SubstancePackageGenerator(arguments.output) as codegen:
                        codegen.visit(ast_sbs)

            except (TranspilerError):
                logger.error(f'Transpilation Failure : {traceback.format_exc()}')
                return -1

        return 0
    except (TranspilerError):
        logger.error(f'Transpilation Failure : {traceback.format_exc()}')
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
            # 'file': {
            #     'class': 'logging.handlers.RotatingFileHandler',
            #     'formatter': 'debug',
            #     'filename': Path('scanbox.log'),
            #     'maxBytes': 1024*1024*1024*1024,
            #     'backupCount': 5,
            #     'encoding': 'utf-8',
            # },
            'null': {
                'class': 'logging.NullHandler',
            }
        },
        'loggers': {
            '__main__': {
                'level': 'DEBUG',
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
