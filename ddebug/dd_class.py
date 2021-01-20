import builtins
import sys
from collections.abc import Callable, Iterable
import inspect

import icecream
from snoop import snoop
import warnings
import watchpoints

try:
    from .errors import set_excepthook, _errors, InteractiveException, set_atexit
except ImportError:
    from errors import set_excepthook, _errors, InteractiveException, set_atexit

# interactive mode check
interactive = hasattr(sys, 'ps1')
if interactive:
    raise InteractiveException()


class IceCreamDebugger(icecream.IceCreamDebugger):
    def _formatArgs(self, callFrame, callNode, prefix, context, args):
        """
        copy of ic._formatArgs in but with operators support after AttributeError
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
            import traceback
            traceback.print_exc()
            prefix = icecream.callOrValue(self.prefix)
            out = prefix + 'Error: ' + err.infoMessage
        self.outputFunction(out)

    def print_class_call(self, name, cls_name, callFrame):
        """
        print class call for d.mincls
        """
        if self.enabled:
            prefix = icecream.callOrValue(self.prefix)

            callNode = icecream.Source.executing(callFrame).node
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


printer = IceCreamDebugger(prefix="dd| ")


def First(mlist):
    """
    :return: mlist[0] if there is
    """
    if mlist:
        return mlist[0]


class ClsDebugger:
    def __init__(self):
        self.w = self.watch = watchpoints.watch.__call__
        self.unw = self.unwatch = watchpoints.watch.unwatch
        self.mincls = self.mc = self._process_class_call

    def __call__(self, *args, from_opp=None, **kwargs):
        """
        call when do dd()

        if first arg is class it gain @snoop on all class functions.

        if first arg is function gain @snoop
        else it do ic(args)

        :return: see _return_args
        """
        first = First(args)
        if from_opp is None:
            from_opp = inspect.currentframe()

        if inspect.isclass(first):
            return self._process_class_snoop(first)

        elif isinstance(first, Callable):
            return snoop(*args[1:], **kwargs)(first)

        elif printer.enabled:
            callFrame = from_opp.f_back
            printer.format_ic(callFrame, *args)
        return self._return_args(args)

    @staticmethod
    def _return_args(args):
        """
        :return: args[0] if that's it. else return all args
        """
        if len(args) == 1:
            return args[0]
        else:
            return args

    @staticmethod
    def _process_class_call(l):
        """
        process class for mincls function
        """
        if not inspect.getmembers(l, predicate=inspect.isfunction):
            class_name = l.__name__
            warnings.warn("you have no method in '%s' class" % class_name)
        for func in inspect.getmembers(l, predicate=inspect.isfunction):
            real_func = func[1]

            def wrapper(*args, **kwargs):
                printer.print_class_call(wrapper.__name__, l.__name__, inspect.currentframe().f_back)
                return real_func(*args, **kwargs)

            wrapper.__doc__ = real_func.__doc__
            wrapper.__name__ = real_func.__name__
            wrapper.__annotations__ = real_func.__annotations__
            wrapper.__defaults__ = real_func.__defaults__
            wrapper.__kwdefaults__ = real_func.__kwdefaults__
            wrapper.__qualname__ = real_func.__qualname__
            wrapper.__module__ = real_func.__module__

            setattr(l, func[0], wrapper)
            # print(f"setattr({l}, {func[0]}, {wrapper})")
        return l

    @staticmethod
    def _process_class_snoop(l):
        """
        do @snoop of all functions on class
        """
        if not inspect.getmembers(l, predicate=inspect.isfunction):
            class_name = l.__name__
            warnings.warn("class '%s' no have any method" % class_name)
        for func in inspect.getmembers(l, predicate=inspect.isfunction):
            real_func = func[1]

            setattr(l, func[0], snoop()(real_func))
            # print(f"setattr({l}, {func[0]}, {wrapper})")
        return l

    @property
    def friendly_traceback_lang(self):
        return _errors.friendly_traceback.get_lang()

    @friendly_traceback_lang.setter
    def friendly_traceback_lang(self, lang):
        _errors.friendly_traceback.set_lang(lang)

    # # # # #
    def install(self, names: Iterable = ("dd",)):
        """
        add dd name to builtins. (like snoop)
        """
        if type(names) == str:
            names = (names,)
        for name in names:
            setattr(builtins, name, self)

    @property
    def enabled(self):
        return watchpoints.watch.enable and snoop.config.enabled and printer.enabled

    @enabled.setter
    def enabled(self, value: bool):
        watchpoints.watch.enable = value
        snoop.config.enabled = value
        printer.enabled = value

    def __mul__(self, other):
        """
        do dd(a) on dd*a
        """
        return self.__call__(other, from_opp=inspect.currentframe())

    def __matmul__(self, other):
        """
        do dd(a) on dd@a
        """
        return self.__call__(other, from_opp=inspect.currentframe())

    def __add__(self, other):
        """
        do dd(a) on dd+a
        """
        return self.__call__(other, from_opp=inspect.currentframe())

    def __lshift__(self, other):
        """
        do dd(a) on dd>>a
        """
        return self.__call__(other, from_opp=inspect.currentframe())

    def __rshift__(self, other):
        """
        do dd(a) on dd<<a
        """
        return self.__call__(other, from_opp=inspect.currentframe())

    def __ror__(self, other):
        """
        do dd(a) on a|dd
        """
        return self.__call__(other, from_opp=inspect.currentframe())

    def __or__(self, other):
        """
        do dd(a) on dd|a
        """
        return self.__call__(other, from_opp=inspect.currentframe())

    def __and__(self, other):
        """
        do dd(a) on a&d
        """
        return self.__call__(other, from_opp=inspect.currentframe())


dd = ClsDebugger()
