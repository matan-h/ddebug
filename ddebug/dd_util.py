"""
utility for ddebug
"""
import io
import os
import re
import sys


def getExecPath() -> str:
    """
    get main script name
    """
    try:
        sFile = sys.modules['__main__'].__file__
    except (AttributeError, KeyError):
        if sys.argv:
            if sys.argv[0]:
                if sys.argv[0].endswith(".py"):
                    sFile = sys.argv[0]
                else:
                    sFile = os.path.basename(sys.argv[0])
            else:
                sFile = "interactive"
        else:
            sFile = os.path.basename(sys.executable)
    return sFile


class DependencyMissing(BaseException):
    """
    Exception that Raise when Missing optional dependency.
    """

    def __init__(self, dependency):
        super().__init__(
            f"Missing optional dependency '{dependency}'. Use `pip install {dependency}` or just install all ddebug optional dependencies by `pip install ddebug[full]`")


class Logger:
    """
    write to io_file and to stream
    """

    def __init__(self, io_file, stream):
        """
        init the Logger object.

        Args:
            io_file: file io to write (will closed and flush)
            stream: std stream to write
        """
        self.stream: io.FileIO = stream
        self.log: io.FileIO = io_file

    def write(self, message):
        """write a messege to stream (in color) and to io_file (without color)"""
        self.stream.write(message)
        self.flush()
        message = ansi_escape.sub('', message)  # never color-print to file
        self.log.write(message)

    def flush(self):
        """flush io_file"""
        self.log.flush()

    def close(self):
        """close io_file"""
        self.log.close()


def rm_friendly_console(string: str) -> str:
    """
    remove the 'If you are using a REPL' from friendly messege

    Args:
        string: friendly messege

    """
    return string.split("If you are using a REPL")[
        0].strip()  # you cant use Friendly console in ddebug file


def post_tb(tb, ddebug_input: str = None):
    """
    post traceback to pdb or pdbr if input-time-out or ddebug_input is True

    Args:
        tb: traceback object to post
        ddebug_input: 1 or True to to set the input always to True,0 or False to to set the input always to False
    """
    timeout = 5
    # i = None
    if ddebug_input is None:
        ddebug_input = os.environ.get("ddebug_pdb", None)
    if type(ddebug_input) == str:
        ddebug_input = {"0": False, "1": True, "true": True, "false": False}.get(ddebug_input, None)

    if ddebug_input is None:
        try:
            import inputimeout
        except ImportError:
            inputimeout = None
        #
        if inputimeout and sys.stdin.isatty():  # can import inputimeout and running on real terminal
            try:
                print(f'press enter within {timeout} seconds to start pdbr\\pdb debugger... > ', file=sys.stderr)
                i = inputimeout.inputimeout(timeout=timeout)
            except (inputimeout.TimeoutOccurred, KeyboardInterrupt, EOFError):
                pass
            else:
                if i not in ("n", "no", "not"):
                    _post_tb(tb)
    #
    else:
        if ddebug_input:
            _post_tb(tb)


def _post_tb(tb):
    try:
        import pdbr
        pdbr.post_mortem(tb)
    except ImportError:
        _start_normal_pdb(tb)
    except Exception as e:
        print("!!! pdbr error: ", repr(e))
        print("starts normal pdb:")
        _start_normal_pdb(tb)


def _start_normal_pdb(tb):
    import pdb
    pdb.post_mortem(tb)


class Exc:
    """
    exc for ddebug - just do `dd.exc()`,`@dd.exc` or `with dd.exc` instead of `dd.print_exception`,`dd.log_error` and `dd.log_error_function`
    """

    def __init__(self, dd_obj):
        """
        init the Exc class with ClsDebugger object

        Args:
            dd_obj (ClsDebugger): ClsDebugger object.
        """
        self.dd = dd_obj

    def __call__(self, obj=None):
        """
        this function is called in `@dd.exc` and in `dd.exc()`
        in `@dd.exc` it will do `@dd.except_error_function`  (functools.wraps with try/except block)
        in `dd.exc()` it will print the exception with `dd.print_exception`

        Args:
            obj (function or None):  function if called by @

        """
        if callable(obj):
            return self.dd.except_error_function(obj)
        else:
            self.dd.print_exception()

    def __enter__(self):
        """
        Returns: the ddebug object
        """
        return self.dd

    def __exit__(self, *exc_info):
        """
        print the exception
        """
        if all(exc_info):  # there is a error
            self.dd.print_exception(exc_info=exc_info)


ansi_escape = re.compile(r'(?:\x1B[@-_]|[\x80-\x9F])[0-?]*[ -/]*[@-~]')
