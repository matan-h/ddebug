import atexit
import bdb
import os
import sys
import time
from contextlib import redirect_stdout, redirect_stderr
from os import path as Path

try:
    from . import _errors
except ImportError:
    import _errors
import logging
import inputimeout
logging.basicConfig()
logger = logging.getLogger("python-Debugger")
logger.setLevel("DEBUG")
log = lambda text=None, *args, **kwargs: logger.info(text, *args, **kwargs)
p = log


def getExecPath():
    try:
        sFile = os.path.abspath(sys.modules['__main__'].__file__)
    except Exception:
        sFile = sys.executable
    return sFile


def _get_excepthook(file=None, pattern="{}-errors"):
    if file is None:
        file = getExecPath()
    file = Path.splitext(file)[0]  # remove ".py"
    error_folder = pattern.format(file)

    # #
    def excepthook(exc_type, exc_value, tb):
        if isinstance(exc_type,bdb.BdbQuit):
            if sys.excepthook == excepthook:
                sys.__excepthook__(exc_type,exc_value,tb)
        _type = lambda x: x.__name__ if type(x) == type else type(x).__name__

        p(f"an {_type(exc_value)} has occurred:\nnow writing error files:\n")

        _mkdir(error_folder)

        for func in _errors.errors_list:
            is_first = _errors.errors_list.index(func) == 0
            name = func.__name__
            if name.startswith("func_"):
                name = name.replace("func_", "", 1)
            name += ".txt"
            #
            file_io = _mkfile(error_folder, name)

            stdout = stderr = file_io
            #
            if is_first:
                stdout, stderr = _errors.Logger(file_io, sys.stdout), _errors.Logger(file_io, sys.stderr)

            with redirect_stdout(stdout):
                with redirect_stderr(stderr):
                    func(exc_type, exc_value, tb)
            file_io.close()
            p(f"done create {name} error file")
        ######
        time.sleep(0.2)
        post_tb(tb)

    return excepthook


def post_tb(tb):
    timeout = 5
    i = None
    try:
        log(f'{timeout} seconds for press enter for start pdb debugger... > ')
        i = inputimeout.inputimeout(timeout=timeout)
    except (inputimeout.TimeoutOccurred, KeyboardInterrupt, EOFError):
        pass
    else:
        if not (i in ("n","no","not")):
            import pdb
            pdb.post_mortem(tb)


def set_excepthook(file=None, pattern="{}-errors"):
    sys.excepthook = _get_excepthook(file=file, pattern=pattern)


def set_atexit(file=None, pattern="{}-errors"):
    def atexit_f():
        if all(sys.exc_info()):
            _get_excepthook(file=file, pattern=pattern)(*sys.exc_info())

    atexit.register(atexit_f)


def _mkdir(folder: str):
    if not Path.exists(folder):
        os.mkdir(folder)


def _mkfile(folder: str, file: str):
    full_name = Path.join(folder, file)
    return open(full_name, "w")


class InteractiveException(OSError):
    def __init__(self):
        super().__init__('Ddebug cant run in Interactive mode. (e.g. python -i).')


if __name__ == '__main__':
    set_atexit()
