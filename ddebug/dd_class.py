import atexit
import bdb
import builtins
import functools
import os
import sys
import time
from typing import Iterable
import inspect

import icecream
import snoop
import snoop.configuration as snoop_configuration
from snoop.formatting import DefaultFormatter
import datetime

from . import dd_util as util
from . import watchlib
from . import richlib

DEBUG = False


class IceCreamDebugger(icecream.IceCreamDebugger):
    def _formatArgs(self, callFrame, callNode, prefix, context, args):
        """
        copy of ic._formatArgs but with operators
        """
        source = icecream.Source.for_frame(callFrame)
        try:
            sanitizedArgStrs = [
                source.get_text_with_indentation(arg)
                for arg in callNode.args]
        except AttributeError:  # callNode(type:BinOp) has no attribute 'args'
            sanitizedArgStrs = [
                source.get_text_with_indentation(callNode.parent)]

        pairs = list(zip(sanitizedArgStrs, args))

        out = self._constructArgumentOutput(prefix, context, pairs)
        return out

    def format_ic(self, callFrame, *args):
        """
        copy of ic.__call__ but getting callFrame.
        """
        try:
            out = self._format(callFrame, *args)
        except icecream.NoSourceAvailableError as err:
            prefix = icecream.callOrValue(self.prefix)
            out = prefix + 'Error: ' + err.infoMessage
        self.outputFunction(out)

    def print_class_call(self, name, cls_name, callFrame):
        """
        print class call for d.mincls
        """
        if self.enabled:
            prefix = icecream.callOrValue(self.prefix)
            executing = icecream.Source.executing(callFrame)
            callNode = executing.node
            if callNode is None:
                self.outputFunction(
                    f"error NoSourceAvailableError(Failed to access the underlying source code for analysis) :call method '{name}' from class '{cls_name}'")
                return

            context = self._formatContext(callFrame, callNode)

            # context = context.split(" at ")
            #
            time = self._formatTime()
            out = prefix + context + f": call method '{name}' from class '{cls_name}'" + time
            self.outputFunction(out)

    @property
    def stream(self):
        if hasattr(self, "_file"):
            return self._file
        else:
            return sys.stderr

    @stream.setter
    def stream(self, value):
        self._file = value
        if value != sys.stderr:
            self.outputFunction = self._output_txt
        else:
            self.outputFunction = icecream.DEFAULT_OUTPUT_FUNCTION

    def _output_txt(self, s):
        self._streamPrint(s)

    def _streamPrint(self, *args):
        file = sys.stderr
        if hasattr(self, "_file"):
            file = self._file
        print(*args, file=file)


def set_snoop_write(output):
    snoop.snoop.config.write = snoop_configuration.get_write_function(output=output, overwrite=False)


printer = IceCreamDebugger(prefix="dd| ")


def First(mlist):
    """
    :return: mlist[0] if there is
    """
    if mlist:
        return mlist[0]


class ClsDebugger:
    def __init__(self, rich_color_system: richlib.Optional[
        richlib.Literal["auto", "standard", "256", "truecolor", "windows"]
    ] = "auto", ):
        # snoop
        self._self_snoop = snoop.snoop()
        self.deep = snoop.pp.deep
        self.ssc = self.snoop_short_config
        # rich
        self._console = richlib.Console(color_system=rich_color_system)
        # rich errors
        self.print_exception = self._console.print_exception
        self.log_error = self.except_error = self._console.logerror
        self.log_error_function = self.except_error_function = self._console.logerror_function
        # rich tools
        self.pprint = self._console.pprint
        self.inspect = self._console.inspect
        self.diff = self._console.diff
        self.locals = self._console.locals
        # watch
        self.w = self.watch = watchlib.watch.__call__
        self.unw = self.unwatch = watchlib.watch.unwatch
        # more
        self.mc = self.mincls

    def _get_call_type(self, first, frame):
        # find @dd
        code_context = inspect.getframeinfo(frame).code_context
        call_type = "()"
        if code_context:
            code_context = code_context[0].strip()

            #####################################
            if callable(first):
                if code_context.startswith(("def", "class")):  # @dd
                    call_type = "@"
        return call_type

    def __call__(self, *args, call_type: str = None, _from_frame=None):
        """
        call when do dd()

        if first arg is class it gain @snoop on all class functions.

        if first arg is function gain @snoop
        else it do ic(args)

        :return: self._return_args() or snoop wrapper
        """
        first = First(args)
        if _from_frame is None:
            _from_frame = inspect.currentframe()
        _from_frame = _from_frame.f_back
        #
        if call_type is None:
            call_type = self._get_call_type(first, _from_frame)
        #
        if call_type == "@":
            return self.process_snoop(first)
        #
        elif printer.enabled:  # and not return yet
            printer.format_ic(_from_frame, *args)
            #
        return self._return_args(args)

    def process_snoop(self, fnc):
        if inspect.isclass(fnc):
            for func in inspect.getmembers(fnc, predicate=inspect.isfunction):
                real_func = func[1]
                #
                setattr(fnc, func[0], self._self_snoop(real_func))
            return fnc
        else:
            return self._self_snoop(fnc)

    @staticmethod
    def _return_args(args):
        """
        :return: args[0] if that it. else return all args
        """
        if len(args) == 1:
            return args[0]
        else:
            return args

    @staticmethod
    def mincls(l):
        """
        process class for mincls function
        """
        for func in inspect.getmembers(l, predicate=inspect.isfunction):
            if func[0].startswith("_"):
                continue

            real_func = func[1]

            @functools.wraps(real_func)
            def wrapper(*args, **kwargs):
                printer.print_class_call(func[0], l.__name__, inspect.currentframe().f_back)
                return real_func(*args, **kwargs)

            setattr(l, func[0], wrapper)
        return l

    # # # # #
    def install(self, names: Iterable = ("dd",)):
        """
        add dd name to builtins. (like snoop)

        :return: self
        """
        if type(names) == str:
            names = (names,)
        for name in names:
            name: str
            setattr(builtins, name, self)
        return self

    # # # #
    def print_stack(self, block=None, context=1):
        stack = inspect.stack(context)[1:]

        self._console.dd_format_frames(stack, block)

    ##
    def add_tmp_stream(self, with_print=True):
        tmp_output_dir = (os.environ.get('TMPDIR', '') or os.environ.get('TEMP', '') or '/tmp')
        tmp_output = os.path.join(tmp_output_dir, "ddebug.txt")
        if with_print:
            self.stream = util.Logger(open(tmp_output, "w"), self.stream)
        else:
            self.stream = open(tmp_output, "w")
        atexit.register(lambda: self.stream.close())
        return tmp_output

    ####
    def add_output_folder(self, with_date=False, with_errors=True, pyfile=None, folder=None):
        from os import path
        if not pyfile:
            pyfile = util.getExecPath()
        if not folder:
            date = "log"
            if with_date:
                date = datetime.datetime.now().strftime('%m-%d-%Y,%H-%M-%S')
            folder = f"{path.splitext(path.basename(pyfile))[0]}_{date}"
        if not path.exists(folder):
            os.mkdir(folder)
        else:
            print(f"WARNING:the output folder \"{folder}\" is already exists.", file=sys.stderr)

        #

        def add_stream(name, std):
            st = open(path.join(folder, f"{name}-log.txt"), "w")
            atexit.register(st.close)
            return util.Logger(st, std)

        printer.stream = add_stream("icecream", sys.stderr)
        self.watch_stream = add_stream("watch", sys.stderr)
        set_snoop_write(add_stream("snoop", sys.stderr))
        self._console.file = add_stream("rich", sys.stdout)
        if with_errors:
            efile = os.path.join(folder, "error")
            if sys.excepthook == sys.__excepthook__:  # sys.excepthook not change
                self.set_excepthook(file=efile, pattern="{}.txt")
            else:
                self.set_atexit(file=efile, pattern="{}.txt")
        return folder

    def snoop_short_config(self, watch=(), watch_explode=(), depth=1):
        self._self_snoop = snoop.snoop(watch, watch_explode, depth)
        return self

    def set_excepthook(self, file=None, pattern="{}-errors.txt", with_file=True):
        sys.excepthook = self._get_excepthook(file=file, pattern=pattern, with_file=with_file)

    def set_atexit(self, file=None, pattern="{}-errors.txt", with_file=True):
        def atexit_f():
            try:
                exctype, value, tb = sys.last_type, sys.last_value, sys.last_traceback
            except AttributeError:  # no exception
                return
            else:
                self._get_excepthook(file=file, pattern=pattern, with_file=with_file)(exctype, value, tb)

        atexit.register(atexit_f)
        return atexit_f

    def _get_excepthook(self, file=None, pattern="{}-errors.txt", with_file=True):
        if with_file:
            if file is None:
                file = util.getExecPath()
            file = os.path.splitext(file)[0]  # remove ".py"
            error_file = pattern.format(file)

        def excepthook(exc_type, exc_value, tb):
            try:
                if isinstance(exc_type, bdb.BdbQuit):
                    return
                if with_file:
                    efile = util.Logger(open(error_file, "w"), sys.stdout)
                    atexit.register(efile.close)
                    self._console.file = efile
                self._console.print_exception(exc_info=[exc_type, exc_value, tb])
            except Exception:
                if DEBUG:
                    import traceback
                    traceback.print_exc()
                #
                print(f"FATAL excepthook error", file=sys.stderr)
                import traceback
                traceback.print_exc()
                print("error when start excepthook. please report this to https://github.com/matan-h/ddebug/issues ",
                      file=sys.stderr)
            time.sleep(0.1)
            util.post_tb(tb)

        return excepthook

    @property
    def enabled(self):
        return watchlib.enable or snoop.snoop.config.enabled or printer.enabled or (not self._console.quiet)

    @enabled.setter
    def enabled(self, value: bool):
        snoop.snoop.config.enabled = value
        printer.enabled = value
        watchlib.enable = value
        self._console.quiet = not value

    @property
    def stream(self):
        return printer.stream

    @stream.setter
    def stream(self, value):
        printer.stream = value
        set_snoop_write(value)
        self.watch_stream = value
        self._console.file = value

    @property
    def watch_stream(self):
        return watchlib.watch.file

    @watch_stream.setter
    def watch_stream(self, value):
        watchlib.watch.file = value

    def snoopconfig(self,
                    out=None,
                    prefix='',
                    columns='time',
                    overwrite=False,
                    color=None,
                    enabled=True,
                    watch_extras=(),
                    replace_watch_extras=None,
                    formatter_class=DefaultFormatter):
        snoop.install(
            builtins=False,
            snoop="snoop",
            pp="pp",
            spy="spy",
            out=out,
            prefix=prefix,
            columns=columns,
            overwrite=overwrite,
            color=color,
            enabled=enabled,
            watch_extras=watch_extras,
            replace_watch_extras=replace_watch_extras,
            formatter_class=formatter_class,
        )
        return self

    @property
    def friendly_lang(self):
        return richlib.friendly.get_lang()

    @friendly_lang.setter
    def friendly_lang(self, lang):
        richlib.friendly.set_lang(lang)

    @property
    def icecream_includeContext(self):
        return printer.includeContext

    @icecream_includeContext.setter
    def icecream_includeContext(self, value):
        printer.includeContext = value

    @property
    def rich_color_system(self):
        return self._console.color_system

    @rich_color_system.setter
    def rich_color_system(self, value: richlib.Optional[
        richlib.Literal["auto", "standard", "256", "truecolor", "windows"]
    ]):
        self._console.color_system = value

    def __mul__(self, other):
        """
        do dd(a) on dd*a
        """
        return self.__call__(other, _from_frame=inspect.currentframe())

    def __matmul__(self, other):
        """
        do dd(a) on dd@a
        """
        return self.__call__(other, _from_frame=inspect.currentframe())

    def __add__(self, other):
        """
        do dd(a) on dd+a
        """
        return self.__call__(other, _from_frame=inspect.currentframe())

    def __lshift__(self, other):
        """
        do dd(a) on dd>>a
        """
        return self.__call__(other, _from_frame=inspect.currentframe())

    def __rshift__(self, other):
        """
        do dd(a) on dd<<a
        """
        return self.__call__(other, _from_frame=inspect.currentframe())

    def __ror__(self, other):
        """
        do dd(a) on a|dd
        """
        return self.__call__(other, _from_frame=inspect.currentframe())

    def __or__(self, other):
        """
        do dd(a) on dd|a
        """
        return self.__call__(other, _from_frame=inspect.currentframe())

    def __and__(self, other):
        """
        do dd(a) on a&d
        """
        return self.__call__(other, _from_frame=inspect.currentframe())

    def __enter__(self, *args, **kwargs):
        self._self_snoop.__enter__(1)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._self_snoop.__exit__(exc_type, exc_val, exc_tb, 1)


dd = ClsDebugger()
