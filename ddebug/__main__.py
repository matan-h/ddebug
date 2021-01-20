try:
    from .dd_class import set_excepthook
except ImportError:
    from dd_class import set_excepthook
import ast
import inspect
import os
import sys

import snoop
import snoop.formatting
import snoop.tracer

# ###############

this_folder = os.path.dirname(__file__)


##################
def run(file):
    set_excepthook(file)
    with open(file, "r") as fileio:
        code = fileio.read()

    code_obj = compile_code(code, file)
    if not code_obj:
        return

    snooplib(file, code, code_obj)


def compile_code(code, file):
    try:
        code_obj = compile(code, file, "exec")
    except SyntaxError:
        sys.excepthook(*sys.exc_info())
        return

    return code_obj


def snooplib(file, code, code_obj):
    """
    this file based on futurecoder snoop.
    """

    snoop.tracer.internal_directories += (this_folder,)

    class FrameInfo(snoop.tracer.FrameInfo):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            code = self.frame.f_code
            self.is_ipython_cell = (
                    code.co_name == '<module>' and
                    code.co_filename == os.path.basename(file)
            )

    snoop.tracer.FrameInfo = FrameInfo
    snoop.formatting.Source._class_local('__source_cache', {}).pop(file, None)

    config = snoop.Config(
        columns=(),
        out=sys.stdout,
        color=True,
    )
    csnoop = config.snoop()
    csnoop.variable_whitelist = set()

    for node in ast.walk(ast.parse(code)):
        if isinstance(node, ast.Name):
            name = node.id
            csnoop.variable_whitelist.add(name)
    csnoop.target_codes.add(code_obj)

    def find_code(root_code):
        """
        Trace all functions recursively
        """
        for sub_code_obj in root_code.co_consts:
            if not inspect.iscode(sub_code_obj):
                continue

            find_code(sub_code_obj)
            csnoop.target_codes.add(sub_code_obj)

    find_code(code_obj)

    with csnoop:
        def execute(code_obj):
            try:
                exec(code_obj, {"__name__": "__main__", "__doc__": None})  # may raise
            except Exception:
                sys.excepthook(*sys.exc_info())

        return execute(code_obj)


if __name__ == '__main__':
    import click


    @click.command(context_settings=dict(help_option_names=["-h", "--help"]), no_args_is_help=True)
    @click.argument("file", type=click.Path(exists=True, dir_okay=False))
    def debug_cli(file):
        """
        debugg python file with snoop
        """
        run(file)


    debug_cli(prog_name="debugg")
