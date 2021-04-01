import os
import re
import sys
import io


def getExecPath():
    try:
        sFile = sys.modules['__main__'].__file__
    except Exception:
        sFile = os.path.basename(sys.executable)
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
        message = ansi_escape.sub('', message)  # never color-print to file
        self.log.write(message)

    def flush(self):
        self.log.flush()

    def close(self):
        self.log.close()


def _rm_friendly_console(string: str):
    return string.split("If you are using the Friendly console")[
        0].strip()  # you cant use "the Friendly console" in ddebug file


def post_tb(tb):
    timeout = 5
    # i = None
    ddebug_input = os.environ.get("ddebug_pdb", None)
    ddebug_input = {"0": False, "1": True, "true": True, "false": False}.get(ddebug_input, None)

    if ddebug_input is None:
        try:
            import inputimeout
        except (ImportError, ModuleNotFoundError) as e:
            print(f"error when import inputimeout: ({e})", file=sys.stderr)
            return
        try:
            print(f'press enter within {timeout} seconds to start pdbr\\pdb debugger... > ', file=sys.stderr)
            i = inputimeout.inputimeout(timeout=timeout)
        except (inputimeout.TimeoutOccurred, KeyboardInterrupt, EOFError):
            pass
        else:
            if not (i in ("n", "no", "not")):
                _post_tb(tb)
    else:
        if ddebug_input:
            _post_tb(tb)


def _post_tb(tb):
    try:
        import pdbr
        pdbr.post_mortem(tb)
    except Exception as e:
        print("!!! pdbr error: ", repr(e))
        print("starts normal pdb:")
        import pdb
        pdb.post_mortem(tb)


ansi_escape = re.compile(r'(?:\x1B[@-_]|[\x80-\x9F])[0-?]*[ -/]*[@-~]')
