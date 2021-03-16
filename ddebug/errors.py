import atexit
import bdb
import sys
import time
from os import path as Path

from . import dd_util as util


def _get_excepthook(file=None, pattern="{}-errors.txt"):
    if file is None:
        file = util.getExecPath()
    file = Path.splitext(file)[0]  # remove ".py"
    error_file = pattern.format(file)

    # #
    def excepthook(exc_type, exc_value, tb):
        try:
            if isinstance(exc_type, bdb.BdbQuit):
                return
            _type = lambda x: x.__name__ if type(x) == type else type(x).__name__

            print(f"an {_type(exc_value)} has occurred:\nnow writing error file:\n", file=sys.stderr)

            with open(error_file, "w") as efile:
                rich_text = util.get_rich(exc_type, exc_value, tb)
                print(rich_text, file=sys.stderr)
                efile.write(rich_text)
                #
                print("\n", file=sys.stderr)
                efile.write("\n\n")
                #
                friendly_traceback_text = util.get_friendly_traceback(exc_type, exc_value, tb)
                print(friendly_traceback_text, file=sys.stderr)
                efile.write(friendly_traceback_text)

            ######
            time.sleep(0.2)
            util.post_tb(tb)
        except Exception as e:
            print(f"FATAL excepthook error ({e}) ", file=sys.stderr)
            print("error when start excepthook. please report this to https://github.com/matan-h/ddebug/issues ",
                  file=sys.stderr)

    return excepthook


def set_excepthook(file=None, pattern="{}-errors.txt"):
    sys.excepthook = _get_excepthook(file=file, pattern=pattern)


def set_atexit(file=None, pattern="{}-errors.txt"):
    def atexit_f():
        try:
            exctype, value, tb = sys.last_type, sys.last_value, sys.last_traceback
        except AttributeError:  # no exception
            return
        else:
            _get_excepthook(file=file, pattern=pattern)(exctype, value, tb)

    atexit.register(atexit_f)
    return atexit_f


if __name__ == '__main__':
    set_atexit()
