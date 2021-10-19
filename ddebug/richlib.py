"""
rich part of ddebug (colors)
"""
import functools
import inspect
import os
import sys
import timeit
from contextlib import contextmanager
from typing import Any, List, Literal, Optional, Callable, Iterable, Union

import friendly_traceback.core
import icecream
import rich
import rich.console
import rich.markdown
import rich.panel
import rich.pretty
import rich.traceback
from rich.console import _COLOR_SYSTEMS_NAMES  # noqa
from rich.scope import render_scope

import ddebug.dd_util as util

try:
    from deepdiff import DeepDiff
except ImportError:
    DeepDiff = None


class Console(rich.console.Console):
    """
    class for all ddebug method that require rich.console
    """

    def __init__(self, color_system: Optional[
        Literal["auto", "standard", "256", "truecolor", "windows"]
    ] = "auto", ):
        super().__init__(color_system=color_system)
        # self.quiet

    @contextmanager
    def logerror(self, show_locals: bool = False):
        try:
            yield
        except Exception:
            self.print_exception(show_locals=show_locals)

    def logerror_function(self, show_locals=False):
        def s_wrapper(f):
            @functools.wraps(f)
            def wrapper(*args, **kwargs):
                try:
                    return f(*args, **kwargs)
                except Exception:
                    self.print_exception(show_locals=show_locals)

            return wrapper

        return s_wrapper(show_locals) if callable(show_locals) else s_wrapper

    def _rich_friendly(self, exc_type, exc_value, tb):
        fr = friendly_traceback.core.FriendlyTraceback(exc_type, exc_value, tb)
        fr.compile_info()

        generic = util.rm_friendly_console(fr.info.get("generic", ''))
        cause = util.rm_friendly_console(fr.info.get("cause", ''))
        suggest = fr.info.get("suggest", '')
        if suggest:
            suggest = "\n" + suggest

        # build Panel
        string = f'{generic}\n{suggest}\n{cause}'

        panel = rich.panel.Panel(rich.markdown.Markdown(string),
                                 title="[traceback.title] Friendly Explanation [dim](call after rich traceback):\n",
                                 expand=False,
                                 padding=(0, 1))
        return panel

    def print_exception(
            self,
            *,
            width: Optional[int] = 100,
            extra_lines: int = 3,
            theme: Optional[str] = None,
            word_wrap: bool = False,
            show_locals: bool = False,
            suppress=(),
            max_frames: int = 100,
            exc_info: List = None
    ) -> None:
        """ Copy of console.print_exception
        Prints a rich render of the last exception and traceback.

                Args:
                    width (Optional[int], optional): Number of characters used to render code. Defaults to 88.
                    extra_lines (int, optional): Additional lines of code to render. Defaults to 3.
                    theme (str, optional): Override pygments theme used in traceback
                    word_wrap (bool, optional): Enable word wrapping of long lines. Defaults to False.
                    show_locals (bool, optional): Enable display of local variables. Defaults to False.
                    suppress (Iterable[Union[str, ModuleType]]): Optional sequence of modules or paths to exclude from traceback.
                    max_frames (int): Maximum number of frames to show in a traceback, 0 for no maximum. Defaults to 100.
                    exc_info (type, value, traceback):current exception exc tuple
                """
        self.quiet = False  # print exception cant be quiet !
        if not exc_info:
            exc_info = sys.exc_info()
        exc_type, exc_value, traceback = exc_info
        if not (exc_type and exc_value and traceback):
            try:
                exc_type, exc_value, traceback = sys.last_type, sys.last_value, sys.last_traceback
            except AttributeError:  # no exception
                return

        rich_trace = rich.traceback.Traceback.from_exception(
            exc_type, exc_value, traceback,
            width=width,
            extra_lines=extra_lines,
            theme=theme,
            word_wrap=word_wrap,
            show_locals=show_locals,
            suppress=suppress,
        )
        self.print(rich_trace)

        # Friendly Explanation
        friendly_trace = self._rich_friendly(exc_type, exc_value, traceback)
        self.print(friendly_trace)

    def diff(self, obj1, obj2, **deep_diff_kws):
        if not DeepDiff:
            raise util.DependencyMissing("deepdiff")
        frame = inspect.currentframe().f_back
        line = frame.f_lineno
        file = frame.f_code.co_filename
        co_name = frame.f_code.co_name
        if line and file:
            file = f"in [yellow]\"{os.path.basename(file)}\"[/]:[blue]{line}[/] in [green][b]{co_name}[/b][/]"
        else:
            file = ''
        diff = DeepDiff(obj1, obj2, **deep_diff_kws).to_dict()
        diff = rich.pretty.Pretty(diff) if diff else "Contents are identical"
        panel = rich.panel.Panel(diff,
                                 title=f"Deep-Diff ([cyan]dd.diff[/] {file}):\n", )
        self.print(panel)

    def inspect(self, obj: Any,
                *,
                title: str = None,
                help: bool = False,
                methods: bool = False,
                docs: bool = True,
                private: bool = False,
                dunder: bool = False,
                sort: bool = True,
                all: bool = False,
                value: bool = True):
        rich.inspect(obj, console=self, title=title, help=help, methods=methods, docs=docs, private=private,
                     dunder=dunder, sort=sort, all=all, value=value)

    def pprint(
            self,
            _object: Any,
            *,
            indent_guides: bool = True,
            max_length: int = None,
            max_string: int = None,
            expand_all: bool = False,
    ):
        rich.pretty.pprint(_object, console=self, indent_guides=indent_guides, max_length=max_length,
                           max_string=max_string,
                           expand_all=expand_all)

    def dd_format_frames(self, stack, block=None):
        panels = []
        for info in stack:
            if block:
                if stack.index(info) >= block:
                    break
            executing = icecream.Source.executing(info.frame)
            text = executing.text()
            if text:
                panels.append(rich.panel.Panel(
                    text,
                    title=f"\"[yellow]{os.path.basename(info.filename)}\"[/]:[blue]{info.lineno}[/] in [green][b]{executing.code_qualname()}[/b][/]"))
        panel = rich.panel.Panel(rich.console.Group(*panels), title="ddStack[cyan](dd.print_stack)[/]")
        self.print(panel)

    def locals(self, sort_keys=False):
        frame = inspect.currentframe().f_back
        line = frame.f_lineno
        file = frame.f_code.co_filename
        if line and file:
            file = f"in \"{os.path.basename(file)}\":{line}"
        else:
            file = ''
        #
        if frame.f_locals:
            self.print(render_scope(
                frame.f_locals,
                title=f'Local Variables (dd.locals {file}):',
                indent_guides=True,
                max_length=10,
                max_string=80,
                sort_keys=sort_keys
            ))

    def timeit(self, f: Callable = None, setup="pass", timer=timeit.default_timer,
               number=timeit.default_number, globals_param=..., print_result=True):
        if f is None:
            return functools.partial(self.timeit, setup=setup, timer=timer, number=number,
                                     globals_param=globals_param,
                                     print_result=print_result)

        @functools.wraps(f)
        def warp(*args, **kwargs):
            func = f
            if args or kwargs:
                func = functools.partial(f, *args, **kwargs)
            _globals = globals_param

            if globals_param is ...:
                _globals = inspect.currentframe().f_back.f_globals

            timeit_result = timeit.timeit(func, setup, timer, number, _globals)
            if print_result:
                text = "{result} - timeit on function {name} - (running {number} times)"

                if self.color_system is not None:
                    text = (text
                            .replace("timeit", "[yellow]timeit[/]")
                            .replace("{name}", "[cyan]{name}[/]")
                            .replace("{number}", "[green]{number}[/]")
                            .replace("{result}", "[blue]{result}[/]")
                            )
                text = text.format(result=timeit_result, name=f.__name__, number=number)
                self.print(text)
            return timeit_result

        return warp

    # color system
    @property
    def color_system(self) -> Optional[str]:
        """
        copy of rich.console.Console.color_system
        """

        if self._color_system is not None:
            return _COLOR_SYSTEMS_NAMES[self._color_system]
        else:
            return None

    @color_system.setter
    def color_system(self, value: Optional[str]):
        if value is not None:
            if value in _COLOR_SYSTEMS_NAMES.values():
                index = list(_COLOR_SYSTEMS_NAMES.values()).index(value)
                color = list(_COLOR_SYSTEMS_NAMES.keys())[index]
                self._color_system = color
            else:
                s = f"{value} is not in rich color-system list.you can set color-system to one of the following:({','.join(list(_COLOR_SYSTEMS_NAMES.values()))})"
                raise KeyError(s)
        else:
            self._color_system = None


if __name__ == '__main__':
    __console = Console()
    __console.diff("r", "r")
    __console.dd_format_frames(inspect.stack())
    with __console.logerror():
        a = "a".upper2()  # noqa
