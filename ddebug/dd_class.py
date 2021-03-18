import atexit
import builtins
import functools
import os
import sys
from typing import Iterable
import inspect

import icecream
import snoop
import snoop.configuration as snoop_configuration
from snoop.formatting import DefaultFormatter
import datetime

from .errors import set_excepthook, set_atexit
from . import dd_util as util
from .watch import watch, watch_callback
import rich


class IceCreamDebugger(icecream.IceCreamDebugger):
    def _formatArgs(self, callFrame, callNode, prefix, context, args):
        """
        copy of ic._formatArgs in but with operators
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
        # ig
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

    def dd_format_frame(self, text, line, filename, code_qualname):
        self.outputFunction(f"""File "{os.path.basename(filename)}", line {line}, in {code_qualname}\n\t{text}""")


def set_snoop_write(output):
    snoop.snoop.config.write = snoop_configuration.get_write_function(output=output, overwrite=False)


printer = IceCreamDebugger(prefix="dd| ")
watch_callback.printer = printer.outputFunction


def First(mlist):
    """
    :return: mlist[0] if there is
    """
    if mlist:
        return mlist[0]


class ClsDebugger:
    def __init__(self):
        self.w = self.watch = watch.__call__
        self.unw = self.unwatch = watch.unwatch
        self.mc = self.mincls
        self.ssc = self.snoop_short_config
        self.set_excepthook = set_excepthook
        self.set_atexit = set_atexit
        self.deep = snoop.pp.deep
        self._self_snoop = snoop.snoop()
        self.inspect = rich.inspect

    def _get_call_type(self, first, frame):
        # find @dd (like q)
        code_context = inspect.getframeinfo(frame).code_context
        call_type = "()"
        if code_context:
            code_context = code_context[0].strip()

            #####################################
            if callable(first):
                if code_context.startswith(("def", "class")):  # @dd
                    call_type = "@"
        return call_type

    def __call__(self, *args, call_type: str = None, _from_frame=None, **kwargs):
        """
        call when do dd()

        if first arg is class it gain @snoop on all class functions.

        if first arg is function gain @snoop
        else it do ic(args)

        :return: see _return_args
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

    def snoop_short_config(self, watch=(), watch_explode=(), depth=1):
        self._self_snoop = snoop.snoop(watch, watch_explode, depth)
        return self

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
    @staticmethod
    def print_stack(reverse=False):
        stack = inspect.stack()[1:]
        #
        q = "'{}'"
        text = icecream.Source.executing(stack[0].frame).text()
        printer.outputFunction(f"ddStack({q.format(text) if text else ''}):")

        if reverse:
            stack = reversed(stack)

        for info in stack:

            executing = icecream.Source.executing(info.frame)
            text = executing.text()
            if text:
                printer.dd_format_frame(text, info.lineno, info.filename,
                                        executing.code_qualname())

    ##
    def add_tmp_stream(self, with_print=True):
        tmp_output_dir = (os.environ.get('TMPDIR') or os.environ.get('TEMP') or '/tmp')
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

        # watch.set_printer(lambda x:print(x,file=add_stream("watch",sys.stderr)))
        printer.stream = add_stream("icecream", sys.stderr)
        self.watch_stream = add_stream("watch", sys.stderr)
        set_snoop_write(add_stream("snoop", sys.stderr))
        if with_errors:
            efile = os.path.join(folder, "error")
            if sys.excepthook == sys.__excepthook__:  # sys.excepthook not change
                self.set_excepthook(file=efile, pattern="{}.txt")
            else:
                self.set_atexit(file=efile, pattern="{}.txt")
        return folder

    @property
    def enabled(self):
        return watch.enable or snoop.snoop.config.enabled or printer.enabled

    @enabled.setter
    def enabled(self, value: bool):
        watch.enable = not value

        snoop.snoop.config.enabled = value
        printer.enabled = value

    @property
    def stream(self):
        return printer.stream

    @stream.setter
    def stream(self, value):
        printer.stream = value
        set_snoop_write(value)
        self.watch_stream = value

    @property
    def watch_stream(self):
        return watch_callback.file

    @watch_stream.setter
    def watch_stream(self, value):
        watch_callback.file = value

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
        return util.friendly.get_lang()

    @friendly_lang.setter
    def friendly_lang(self, lang):
        util.friendly.set_lang(lang)

    @property
    def icecream_includeContext(self):
        return printer.includeContext

    @icecream_includeContext.setter
    def icecream_includeContext(self, value):
        printer.includeContext = value

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
