import io

import cheap_repr

from ddebug import dd
from ddebug.dd_util import ansi_escape

dd.rich_color_system = None


def _remove_ansi(value):
    return ansi_escape.sub('', value)


class TestDD:
    def test_dd_ic(self):
        class A:
            def foo(self, n):
                return n + 333

        with io.StringIO() as tmp:
            dd.stream = tmp
            dd(A().foo(123))
            dd(A())
            dd(A().foo)
            dd()
            a = "a"
            b = "b"
            c = dd(dd(a) + dd(b))
            dd(c)
            dd()
            #
            a = "a"
            b = dd + a
            b = dd * a
            # b = dd @ a
            b = dd >> a
            b = dd << a
            b = a | dd
            b = dd | a
            b = dd & a
            dd(A.foo)
            for line in tmp.getvalue().strip().split("\n"):
                #
                assert line.startswith("dd|"), f"line '{line}' is not start with 'dd|' \ntmp:{tmp.getvalue()}"
                assert b == a, "dd not return the value"
            # assert (map(lambda x:x.startswith("dd |"),tmp.getvalue().split("\n")))

    def test_dd_enabled(self):
        with io.StringIO() as tmp:
            dd.stream = tmp
            dd.enabled = False
            dd("gffg")

            @dd
            def foo(): pass

            foo()

            class X: pass

            dd(X)
            a = ""
            dd.w(a)
            a = {"a": 1, "n": 2}
            dd.pprint(a)
            dd.diff(a, a)
            dd.diff(a, "gs")
            dd.inspect(a)
            dd.enabled = True
            assert tmp.getvalue() == '', f"\"{tmp.getvalue()}\" is not empty"

    def test_dd_watch(self):
        with io.StringIO() as tmp:
            dd.stream = tmp
            a = []
            dd.w(a)
            a = {}
            a = 1
            a += 1
            assert tmp.getvalue().count("Watch trigger") == 3

    def test_dd_rich(self):
        with io.StringIO() as tmp:
            dd.stream = tmp
            a = "string to inspect"
            dd.inspect(a)
            value = tmp.getvalue()
            assert "str(object='') ->" in _remove_ansi(value)
            assert a in _remove_ansi(value)

        with io.StringIO() as tmp:
            dd.stream = tmp
            dd.diff("LOGGER".split(), "LOG".split())
            value = tmp.getvalue()
            value = _remove_ansi(value)
            assert "values_changed" in value
            assert "{" in value
            assert "}" in value
            assert "dd.diff" in value

        with io.StringIO() as tmp:
            dd.stream = tmp
            a = 60
            b = 70
            dd.locals()
            value = _remove_ansi(tmp.getvalue())
            assert "a = 60" in value
            assert "b = 70" in value
            assert "dd.locals" in value

    def test_dd_snoop(self):
        with io.StringIO() as tmp:
            dd.stream = tmp

            @dd
            def foo():
                pass

            foo()
            value = _remove_ansi(tmp.getvalue())
            assert ">>> call" in value.lower()
            assert "none" in value.lower()
            assert __file__ in value

        with io.StringIO() as tmp:
            dd.stream = tmp

            @dd
            def foo(n):
                return n + 333

            assert foo(123) == 456
            value = _remove_ansi(tmp.getvalue())
            assert "<<< Return value from" in value
            assert value.strip().endswith("456")
        with io.StringIO() as tmp:
            dd.stream = tmp

            @dd
            class X:
                def __init__(self):
                    pass

                def a(self):
                    return "$$$"

            x = X()
            value = _remove_ansi(tmp.getvalue())
            assert "__init__" in value
            x.a()
            value = _remove_ansi(tmp.getvalue())
            assert "a" in value
            assert "$$$" in value

    def test_ssc(self):
        with io.StringIO() as tmp:
            dd.stream = tmp
            a = "hello {}"

            @dd.ssc(watch="_a.format('world')")
            def foo(_a):
                pass

            foo(a)
            value = _remove_ansi(tmp.getvalue())
            assert cheap_repr.cheap_repr('hello world') in value
        with io.StringIO() as tmp:
            dd.stream = tmp

            @dd.ssc(watch_explode=["_foo"])
            def bar(_foo):
                pass

            argv = [1, 2, "5", 6, 9]
            bar(argv)
            value = _remove_ansi(tmp.getvalue())

            for arg in argv:
                index = argv.index(arg)
                assert f"_foo[{index}] = {cheap_repr.cheap_repr(arg)}" in value
        with io.StringIO() as tmp:
            dd.stream = tmp

            @dd.ssc(watch=["self.b"])
            class X:
                def a(self):
                    pass

                @property
                def b(self):
                    return "%%%"

            x = X()
            x.a()
            assert "self.b = %s" % cheap_repr.cheap_repr("%%%")

    def test_dd_ii(self):
        with io.StringIO() as tmp:
            dd.stream = tmp
            dd.icecream_includeContext = True
            dd("a")
            assert "test_dd_ii" in tmp.getvalue()
            dd.icecream_includeContext = False

    def test_dd_error(self):
        with io.StringIO() as tmp:
            dd.stream = tmp
            try:
                a = 1 / 0  # noqa
            except Exception:
                dd.print_exception()
                value = _remove_ansi(tmp.getvalue())
                assert "a = 1 / 0" in value
                assert "Traceback (most recent call last)" in value
                assert "Friendly Explanation" in value
                assert "dividing" in value

    def test_dd_stack(self):
        with io.StringIO() as tmp:
            dd.stream = tmp

            def a():
                b()

            def b():
                c()

            def c():
                d()

            def d():
                dd.print_stack(block=5)

            a()

            value = tmp.getvalue()
            for l in list("abcd"):
                assert "." + l in value
                assert l + "()" in value
                assert "dd.print_stack" in value

    def test_mincls(self):
        with io.StringIO() as tmp:
            dd.stream = tmp

            @dd.mincls
            class X:
                def a(self):
                    pass

                def b(self):
                    pass

                def c(self):
                    pass

            x = X()
            x.a()
            x.b()
            x.c()
            value = tmp.getvalue()
            for l in list("abc"):
                dd_out = (value.split("\n")["abc".index(l)])
                assert "dd| " in dd_out
                assert repr("X") in dd_out
                assert "at " in dd_out

    def test_dd_color(self):
        with io.StringIO() as tmp:
            dd.stream = tmp
            dd.rich_color_system = "256"
            dd.print_stack(block=3)
            assert "\x1b" in tmp.getvalue()
        with io.StringIO() as tmp:
            dd.stream = tmp
            try:
                0 / 1
            except Exception:
                dd.print_exception()
                value = tmp.getvalue()
                assert "\x1b" in value
        dd.rich_color_system = None

    def test_dd_timeit(self):
        with io.StringIO() as tmp:
            dd.stream = tmp

            @dd.timeit
            def add(a, b):
                a + b

            n = add(123, 333)
            assert n != 456
            assert type(n) == float
            value = tmp.getvalue()  # 0.0... - timeit on function add - (running 1000000 times)
            assert "times" in value
            assert " add " in value


if __name__ == '__main__':
    import pytest

    pytest.main()
