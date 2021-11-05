"""
watch for ddebug (dd.watch,dd.unwatch)
"""
import importlib
import sys

from .dd_util import DependencyMissing

try:
    import watchpoints.watch_print
except ImportError:
    watchpoints = None

if watchpoints:
    enable = True


    class WatchCallBack(watchpoints.watch_print.WatchPrint):
        """
        custom WatchPrint
        """
        def __init__(self, file=sys.stderr, stack_limit=None):
            super().__init__(file, stack_limit)
            self.source_printer = self.printer
            self.printer = self._printer

        def __call__(self, _frame, elem, exec_info):
            _file_string = f"Watch trigger ::: File \"{exec_info[1]}\", line {exec_info[2]}, in {exec_info[0]}"
            p = self.printer
            p(_file_string)
            alias = "error:cant find variable name"
            if elem.alias:
                # p(f"{elem.alias}:")
                alias = elem.alias
            elif elem.default_alias:
                # p(f"{elem.default_alias}:")
                alias = elem.default_alias
            print_format = "\t{}:was {} is now {} "
            p(print_format.format(alias, repr(elem.prev_obj), repr(elem.obj)))

        def _printer(self, obj):
            if enable:
                self.source_printer(obj)


    # replace `WatchPrint` by `WatchCallBack`.
    # watchpoints.watch.config() # TODO
    importlib.import_module("watchpoints.watch").WatchPrint = WatchCallBack
    watch = watchpoints.watch
else:
    def watch(*_args, **_kwargs):
        """
        raise DependencyMissing

        Raises:
            DependencyMissing - watchpoints.
        """
        raise DependencyMissing("watchpoints")


    watch.unwatch = watch
    enable = False


def main():
    class X:
        pass

    a = "prev_a"
    b = "prev_b"
    x = X()
    watch(a, file="a.txt")
    watch(b, x)
    a = "ab"
    b = "ba"
    x.s = 5


if __name__ == '__main__':
    main()
