"python library for debug python file"
try:
    from .dd_class import dd, ClsDebugger, set_excepthook,set_atexit
except ImportError:
    from dd_class import dd, ClsDebugger, set_excepthook,set_atexit

__version__ = "0.0.1"
__all__ = ["dd", "ClsDebugger", "set_excepthook", "set_atexit"]

if __name__ == "__main__":
    def simple_example():
        @dd  # equal to do @snoop on all class function
        class ExampleClass:
            def __init__(self):
                self.s = lambda :None
            def foo(self, n=456):
                return n + 333

        e = ExampleClass()
        e.foo()
        # # # #
        dd("".join(['c', 'a', 'n', ' ', 'b', 'e', ' ', 'i', 'c', 'e', 'c', 'r', 'e', 'a', 'm', "."]))

        # can be icecream. (this is that this line printing)

        # # # #
        @dd.mincls  # can be only calls to class (based on icecream)
        class ExampleClass:
            def foo(self, n=456):
                return n + 333

        dd(ExampleClass().foo(123))
        a = []
        dd.watch(a)  # can watch variables (with watchpoints)
        a = "a"
        b = "b"
        dd(dd(a), dd(b))

        set_excepthook()
        # after error it generate error folder with 4 txt files:
        # better_exceptions.txt using "better_exceptions" library
        # friendly_traceback.txt using "friendly_traceback" library
        # stackprinter.txt using "stackprinter" library
        # traceback.txt - normal traceback
        # all this files is for the user(you) can view the error Conveniently. (each of those libraries is comfortable
        # for anther type of errors)


    simple_example()
