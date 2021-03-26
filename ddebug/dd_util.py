import multiprocessing
import os
import sys
import time

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
    try:
        fr = friendly.core.FriendlyTraceback(exc_type, exc_value, tb)
        fr.compile_info()
        generic = _rm_friendly_console(fr.info["generic"])
        cause = _rm_friendly_console(fr.info.get("cause", str()))
        suggest = fr.info.get("suggest", str())
        return f"{generic}\n\n{cause}\n{suggest}"
    except (Exception,SystemExit):
        return 'Internal problem in Friendly.\nPlease report this issue.'


def _rm_friendly_console(string: str):
    return string.split("If you are using the Friendly console")[0].strip()  # you cant use "the Friendly console" in ddebug file


def post_tb(tb):
    timeout = 5
    # i = None
    try:

        print(f'{timeout} seconds for press enter for start pdb debugger... > ', file=sys.stderr)
        i = InputTimeOut(timeout=timeout).run()
    except Exception:
        pass
    else:
        if i:
            if not (i in ("n", "no", "not")):
                import pdb
                pdb.post_mortem(tb)


class InputTimeOut:
    def __init__(self, prompt: str = '', timeout: float = 30):
        self.prompt = prompt
        self.timeout = timeout

    def _input_process(self, stdin_fd, sq):
        sys.stdin = os.fdopen(stdin_fd)
        try:
            inp = input(self.prompt)
            sq.put(inp)
        except Exception:
            sq.put(None)

    def run(self):
        sq = multiprocessing.Queue()
        p = multiprocessing.Process(target=self._input_process, args=(sys.stdin.fileno(), sq))
        p.start()
        t = time.time()
        inp = None
        while True:
            if not sq.empty():
                inp = sq.get()
                break
            if time.time() - t > self.timeout:
                break
        p.terminate()
        sys.stdin = os.fdopen(sys.stdin.fileno())
        print()
        return inp
