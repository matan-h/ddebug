"""
main file for ddebug.
"""
import atexit
import bdb
import builtins
import datetime
import functools
import inspect
import os
import sys
import traceback
from os import path
from time import sleep
from types import FrameType, FunctionType
from typing import Any, Iterable, Literal, Optional, Sequence, Type, Union

import icecream
import snoop
import snoop.configuration as snoop_configuration

#
from ddebug import dd_util as util
from ddebug import richlib, watchlib


class _IceCreamDebugger(icecream.IceCreamDebugger):
    """
    class for overwrite some icecream methods to make them match ddebug
    """

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
        print class call for dd.mincls
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
        """
        Get/Set icecream stream
        """
        if hasattr(self, "_file"):
            return self._file
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


def set_snoop_write(output) -> None:
    """
    set snoop stream to output
    Args:
        output (): stream
    Returns:
        None

    """
    snoop.snoop.config.write = snoop_configuration.get_write_function(output=output, overwrite=False)


def _first(mlist: Sequence) -> Optional[Union[Any, str]]:
    """
    return first element in list

    Args:
        mlist (Sequence): the list

    Returns:
        Optional[Union[Any, str]]:first element in mlist if there is.

    """
    if mlist:
        return mlist[0]


class ClsDebugger:

    def __init__(self, rich_color_system: richlib.Optional[
        richlib.Literal["auto", "standard", "256", "truecolor", "windows"]
    ] = "auto", ):
        """
        main class for ddebug.

        Args:
            rich_color_system (str): rich color system. can be  auto,standard,256,truecolor or windows. see https://rich.readthedocs.io/en/stable/console.html#color-systems
        """
        # snoop
        self._self_snoop = snoop.snoop()
        self.deep = snoop.pp.deep
        """
        copy from snoop.pp.deep; can trace subexpressions.see https://github.com/alexmojaki/snoop#ppdeep-for-tracing-subexpressions
        """
        self.ssc = self.snoop_short_config
        """
        shortcut for `dd.snoop_short_config`
        """
        # rich
        self._console = richlib.Console(color_system=rich_color_system)
        self._ic = _IceCreamDebugger(prefix="dd| ")
        # rich errors
        self.print_exception = self._console.print_exception
        """
        function for print exception (with rich and friendly) in rich after the exception rises """
        self.log_error = self.except_error = self._console.logerror

        """
        contextmanager for print exception if exception raises in with block
        """
        self.log_error_function = self.except_error_function = self._console.logerror_function
        """
        function wrapper for print exception if exception raises in the function
        """
        self.exc = util.Exc(self)
        """
        shortcut for all `print_exception` types - can use as `print_exception`,`log_error` and `log_error_function`.
        """
        # rich tools
        self.pprint = self._console.pprint
        """
        function for rich pretty print value
        """
        self.inspect = self._console.inspect
        """
        function for rich.inspect - Inspect any Python object.see https://rich.readthedocs.io/en/stable/introduction.html#rich-inspect
        """
        self.diff = self._console.diff
        """
        function for pretty print of DeepDiff with rich
        """
        self.locals = self._console.locals
        """
        function for pretty print all locals with rich
        """
        self.time = self.timeit = self._console.timeit
        # watch
        self.w = self.watch = watchlib.watch.__call__
        """
        shortcut for watchlib.watch
        """
        self.unw = self.unwatch = watchlib.watch.unwatch
        """
        shortcut for watchlib.unwatch
        """
        # more
        self.mc = self.mincls
        """
        shortcut for `dd.mincls`
        """

    @staticmethod
    def _get_call_type(first, frame: FrameType) -> str:
        """
        find @dd or dd()

        Args:
            first: first argument
            frame: call frame

        Returns: () or @

        """
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

    def __call__(self, *args, call_type: Optional[Literal["@", "()"]] = None, _from_frame=None) -> Union[
        str, tuple, FunctionType]:
        """
        call on dd() or dd+-@ etc.

        if first arg is class it gain @snoop on all class functions.
        if first arg is function gain @snoop.

        Args:
            *args: args to print.
            call_type (Optional[Literal["@", "()"]]): "()","@" or None : if None the call_type will be detect automatic
            _from_frame: if this called from operation (e.g. dd+@*) it pass it frame to here

        Returns:
            Union[str,tuple,FunctionType]:the first element if the args had only one element,also if call_type become @ it return snoop wrapper if the first argument is function or class-snoop-wrapper if the first argument is class

        """

        first = _first(args)
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
        if self._ic.enabled:  # and not return yet
            self._ic.format_ic(_from_frame, *args)
            #
        return self._return_args(args)

    def process_snoop(self, fnc: Union[FunctionType, Type]) -> Union[FunctionType, Type]:
        """
        append @snoop to function or @snoop to all functions in class

        Args:
            fnc: the function or class

        Returns:
            Union[FunctionType,Type]: the class or the function with @snoop

        """
        if inspect.isclass(fnc):
            for func in inspect.getmembers(fnc, predicate=inspect.isfunction):
                real_func = func[1]
                #
                setattr(fnc, func[0], self._self_snoop(real_func))
            return fnc
        else:
            return self._self_snoop(fnc)

    @staticmethod
    def _return_args(args: Sequence) -> Union[Sequence, Any]:
        """
        return
            args[0] if that it. else return all args
        Args:
            args (Sequence): args to return

        Returns:
            args[0] if that it. else return all args
        """
        if len(args) == 1:
            return args[0]
        else:
            return args

    def mincls(self, l: Type) -> Type:
        """
        process class for see the functions call

        Args:
            l (Type): the class

        Returns:
            the class with the mincls wrapper
        """
        for func in inspect.getmembers(l, predicate=inspect.isfunction):
            if func[0].startswith("_"):
                continue

            real_func = func[1]

            @functools.wraps(real_func)
            def wrapper(*args, **kwargs):
                self._ic.print_class_call(func[0], l.__name__, inspect.currentframe().f_back)
                return real_func(*args, **kwargs)

            setattr(l, func[0], wrapper)
        return l

    @staticmethod
    def breakpoint():
        """
        breakpoint with pdbr if its installed else with pdb
        """
        try:
            import pdbr as debugger
        except ImportError:
            import pdb as debugger
        debugger.set_trace()

    # # # # #
    def install(self, names: Iterable = ("dd",)):
        """
        make dd available in every file (without needing to import ddebug) by add dd name to builtins.

        Args:
            names (Iterable):Iterable array with names for ddebug values . Defaults to tuple with "dd"

        Returns:
             ClsDebugger:the ClsDebugger object (dd)
        """
        if type(names) == str:
            names = (names,)
        for name in names:
            name: str
            setattr(builtins, name, self)
        return self

    # # # #
    def print_stack(self, block: int = None, context=1):
        """
        print the inspect.stack with rich

        Args:
            block: block after X
            context:context value for `inspect.stack` function
        """
        stack = inspect.stack(context)[1:]

        self._console.dd_format_frames(stack, block)

    ##
    def add_tmp_stream(self, with_print=True) -> str:
        """
        add/set ddebug stream to tmp file named `ddebug.txt`.

        Args:
            with_print (bool): if True the tmp file write in addition to the stdout

        Returns:
            str:the tmp file name
        """
        tmp_output_dir = (os.environ.get('TMPDIR', '') or os.environ.get('TEMP', '') or '/tmp')
        tmp_output = os.path.join(tmp_output_dir, "ddebug.txt")
        if with_print:
            self.stream = util.Logger(open(tmp_output, "w"), self.stream)
        else:
            self.stream = open(tmp_output, "w")
        atexit.register(self.stream.close)
        return tmp_output

    ####
    def add_output_folder(self, with_date: bool = False, with_errors: bool = True, pyfile: str = None,
                          folder: str = None) -> str:
        """
        set ddebug stream to the normal std plus output folder (named the main script name) with 4 txt file:

        * `watch-log` - output from `dd.<un>watch`
        * `snoop-log` - output from `@dd` on class or function and from `dd.deep`
        * `icecream-log` - output from `dd()` and `@dd.mincls`.
        * `rich-log` - output from `dd.pprint`,`dd.inspect`,`dd.diff` and `dd.print_stack()`

        It will also set excepthook or atexit to create a file named `error.txt` in this folder.
        Pass `with_errors=False` to this function to prevent this.

        Args:
            with_date:if True it will create the folder with the data Defaults to False
            with_errors: if False it prevent create excepthook or atexit. Defaults to True
            pyfile: the python file to prevent the auto detect. Defaults to None
            folder: the name of the output folder.Defaults to None

        Returns:
            str: the output folder name
        """
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

        self._ic.stream = add_stream("icecream", sys.stderr)
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
        """
        config ddebug Common arguments

        Args:
            watch: show values of arbitrary expressions by specifying them as a string e.g. @dd(watch=('foo.bar', 'self.x["whatever"]'))
            watch_explode:Expand variables or expressions to see all their attributes or items of lists/dictionaries:
            depth:snoops deeper calls made by the function/block you trace. The default is 1, meaning no inner calls, so pass something bigger.
            ... : (the Args description copied from snoop )

        Returns:
            ClsDebugger:the ClsDebugger object (dd). so can call snoop after that e.g. @dd.ssc(('foo.bar', 'self.x["whatever"]'))


        """
        self._self_snoop = snoop.snoop(watch, watch_explode, depth)
        return self

    def set_excepthook(self, file: str = None, pattern="{}-errors.txt", with_file=True):
        """
        set excepthook for rich print exception.

        Args:
            file (str): the python filename. Defaults to None
            pattern (str): pattern (with "{}" ) for format the python file basename. Defaults to "{}-errors.txt"
            with_file: write the excepthook to the txt file create with the file and the pattern.Defaults to True
        """
        sys.excepthook = self._get_excepthook(file=file, pattern=pattern, with_file=with_file)

    def set_atexit(self, file=None, pattern="{}-errors.txt", with_file=True):
        """
        same as dd.set_excepthook but set the atexit hook instead.
        """

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
                #
                print("FATAL excepthook error", file=sys.stderr)
                traceback.print_exc()
                print("error when start excepthook. please report this to https://github.com/matan-h/ddebug/issues ",
                      file=sys.stderr)
            sleep(0.1)
            util.post_tb(tb)

        return excepthook

    @property
    def enabled(self) -> bool:
        """
        Get/Set ddebug enable
        Getting this value will be True if any of ddebug outputs (watchpoint,snoop,icecream and rich) enabled.
        Setting this value to X will set enabled of all ddebug outputs to X
        """
        return watchlib.enable or snoop.snoop.config.enabled or self._ic.enabled or (not self._console.quiet)

    @enabled.setter
    def enabled(self, value: bool):
        snoop.snoop.config.enabled = value
        self._ic.enabled = value
        watchlib.enable = value
        self._console.quiet = not value

    @property
    def stream(self):
        """
        Get/Set ddebug enable
        Getting this value will return the icecream stream.
        Setting this value to X will set all ddebug outputs (watchpoint,snoop,icecream and rich) to X
        """
        return self._ic.stream

    @stream.setter
    def stream(self, value):
        self._ic.stream = value
        set_snoop_write(value)
        self.watch_stream = value
        self._console.file = value

    @property
    def watch_stream(self):
        """
        Get/Set watchpoint stream.
        """
        return watchlib.watch.file

    @watch_stream.setter
    def watch_stream(self, value):
        watchlib.watch.file = value

    def snoopconfig(self, *args, **kwargs):
        """
        config snoop by the `snoop,install` method.
        see for arguments https://github.com/alexmojaki/snoop/#output-configuration

        Args:
            *args: see snoop.install
            **kwargs: see snoop.install

        Returns:
            ClsDebugger:the ClsDebugger object (dd)

        """
        snoop.install(
            builtins=False,
            *args, **kwargs
        )
        return self

    @property
    def friendly_lang(self):
        """
        Get/Set friendly-traceback language
        """
        return richlib.friendly_traceback.get_lang()

    @friendly_lang.setter
    def friendly_lang(self, lang):
        richlib.friendly_traceback.set_lang(lang)

    @property
    def icecream_includeContext(self):
        """
        Get/Set icecream includeContext (dd() calls filename, line number, and parent function to dd output.)
        """
        return self._ic.includeContext

    @icecream_includeContext.setter
    def icecream_includeContext(self, value):
        self._ic.includeContext = value

    @property
    def rich_color_system(self):
        """
        Get/Set rich_color_system

        rich_color_system: rich color system. can be auto,standard,256,truecolor or windows. see https://rich.readthedocs.io/en/stable/console.html#color-systems
        """
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
        """
        do snoop.__enter__ on dd.__enter__ (enter `with` block)
        """
        self._self_snoop.__enter__(1)

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        do snoop.__exit__ on dd.__exit__ (exit `with` block)
        """
        self._self_snoop.__exit__(exc_type, exc_val, exc_tb, 1)


# create the dd object
dd: ClsDebugger = ClsDebugger()
"""
main callable object for ddebug.it can do dd(*args) , @dd. with dd:, and had operators like dd@a,dd+a.
it had some real method e.g. print_exception and print_stack,etc.
and some properties e.g. stream,friendly_lang and icecream_includeContext
"""
