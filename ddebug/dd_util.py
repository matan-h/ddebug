import os
import sys

import friendly
import friendly.core

import io


def getExecPath():
    try:
        sFile = os.path.abspath(sys.modules['__main__'].__file__)
    except Exception:
        sFile = sys.executable
    return sFile


class Logger:
    """
    write to io_file and to stream
    """

    def __init__(self, io_file, stream):
        self.stream: io.FileIO = stream
        self.log: io.FileIO = io_file

    def write(self, message):
        self.stream.write(message)
        self.flush()
        self.log.write(message)

    def flush(self):
        self.log.flush()

    def close(self):
        self.log.close()


def get_rich(exc_type, exc_value, tb):
    from rich.console import Console
    import rich
    from rich.traceback import Traceback
    with io.StringIO() as output:
        console = Console() or rich.get_console()
        console.file = output
        console.print(Traceback.from_exception(exc_type, exc_value, tb))
        value = output.getvalue()
    return value


def get_friendly(exc_type, exc_value, tb):
    friendly_obj = friendly.core.FriendlyTraceback(exc_type, exc_value, tb)
    friendly_obj.compile_info()
    return friendly_obj.info["generic"]


def post_tb(tb):
    timeout = 5
    # i = None
    try:
        import inputimeout
    except (ImportError, ModuleNotFoundError) as e:
        print(f"error when import inputimeout: ({e})", file=sys.stderr)
        return
    try:

        print(f'{timeout} seconds for press enter for start pdb debugger... > ', file=sys.stderr)
        i = inputimeout.inputimeout(timeout=timeout)
    except (inputimeout.TimeoutOccurred, KeyboardInterrupt, EOFError):
        pass
    else:
        if not (i in ("n", "no", "not")):
            import pdb
            pdb.post_mortem(tb)


class InteractiveException(OSError):
    def __init__(self):
        super().__init__('Ddebug cant run in Interactive mode. (e.g. python -i).')


regex_spaces = "[ \t]*"
