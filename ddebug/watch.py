import atexit
import sys
from watchpoints.watch import Watch as _Watch

# from watchpoints.watch_print import WatchPrint as _WatchPrint
# from watchpoints import watch

get_printer = lambda file=sys.stderr: lambda obj: print(obj, file=file)


class WatchCallBack:
    def __init__(self, file=sys.stderr, stack_limit=None):
        self._file = file
        self.stack_limit = stack_limit
        self.printer = get_printer(self.file)

    @property
    def file(self):
        return self._file

    @file.setter
    def file(self, value):
        self._file = value
        self.printer = get_printer(value)

    def callback(self, _frame, elem, exec_info):
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


class Watch(_Watch):
    def custom_callback(self, frame, elem, exec_info):
        if self.enable:
            watch_callback.stack_limit = self.stack_limit
            watch_callback.callback(frame, elem, exec_info)


watch_callback = WatchCallBack()
watch = Watch()
watch.config(callback=watch.custom_callback)

# watch.config(
#    callback=watch.custom_callback
# )

if __name__ == '__main__':
    io1 = open("../tt.txt", "w")
    atexit.register(io1.close)
    io2 = open("../t.txt", "w")
    atexit.register(io2.close)


    class X:
        pass


    a = "prev_a"
    b = "prev_b"
    x = X()
    watch(a,file=io1)
    watch(b,x,file=io2)
    a = "ab"
    b = "ba"
    x.s = 5

