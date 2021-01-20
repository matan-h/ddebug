import io
import os
import sys
# from contextlib import redirect_stdout, redirect_stderr

import friendly_traceback
import stackprinter
import better_exceptions

better_exceptions.SUPPORTS_COLOR = False


class Logger:
    def __init__(self, io_file, stream):
        self.stream = stream
        self.log = io_file

    def write(self, message):
        self.stream.write(message)
        self.flush()
        self.log.write(message)

    def flush(self):
        self.stream.flush()
        # this flush method is needed for python 3 compatibility.
        # this handles the flush command by doing nothing.
        # you might want to specify some extra behavior here.


def func_better_exceptions(exc_type, exc_value, tb):
    better_exceptions.STREAM = sys.stdout
    better_exceptions.excepthook(exc_type,exc_value,tb)


def func_stackprinter(exc_type, exc_value, tb):
    stackprinter.show((exc_type,exc_value,tb))


def func_friendly_traceback(exc_type, exc_value, tb):
    friendly_traceback.session.exception_hook(exc_type,exc_value,tb)


def func_traceback(exc_type, exc_value, tb):
    import traceback
    traceback.print_exception(exc_type,exc_value,tb)


# errors_list = [func_pretty_errors, func_stackprinter, func_friendly_traceback]
errors_list = [func_friendly_traceback,func_traceback,func_stackprinter, func_better_exceptions]
