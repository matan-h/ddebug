# ddebug
ddebug is a python library for cool debugging of python progams.

ddebug is both
[icecream](https://github.com/gruns/icecream) and
[snoop](https://github.com/alexmojaki/snoop)
but simple and quick in the style of [q](https://github.com/zestyping/q)
## Installation
Install using pip: ```(python -m) pip install -i https://test.pypi.org/simple/ ddebug```



## Simple Example
```python
from ddebug import dd
@dd #do @snoop on a function
def foo(n):
    return n+333
@dd # do @snoop on all class functions
class A:
    def a(self):
        pass

dd(foo(123)) # use like icecream.
```
output:
```shell
12:30:49.47 >>> Call to foo in File "python-file.py", line 3
12:30:49.47 ...... n = 123
12:30:49.47    3 | def foo(n):
12:30:49.47    4 |     return n+333
12:30:49.47 <<< Return value from foo: 456
dd| foo(123): 456
```
## more options

### min cls:
Sometimes you don't want to view all the class functions internal process. Then you can use mincls option to just see the function call:
```python
from ddebug import dd
@dd.mincls
class A:
    def a(self):
        pass

a = A()
a.a()
```
Output:
```shell
dd| python-file.py:8 in <module>: call method 'a' from class 'A' at 11:34:15.383
```
### Concatenating
```python
from ddebug import dd
a = "a"
b = "b"
dd(dd(a)+dd(b))
```
Output:
```shell
dd| a: 'a'
dd| b: 'b'
dd| dd(a)+dd(b): 'ab'
```

### Tracebacks
In `ddebug` there is a more detailed traceback option:
```python
from ddebug import set_excepthook
#place at start of program
set_excepthook()
# same as
from ddebug import dd
#place at start of program
dd.set_excepthook()
```
Then when an error occurrs `ddebug` creates a folder named `<file>-errors`
and writes 4 traceback files:
* friendly_traceback.txt - [friendly_traceback](https://github.com/aroberge/friendly-traceback) (also prints)
* stackprinter.txt - [stackprinter](https://github.com/alexmojaki/stackprinter)
* better_exceptions.txt - [better_exceptions](https://github.com/Qix-/better-exceptions)
* traceback.txt - the normal traceback

In addition, you can press Enter within the first 5 seconds after exception and it will open the standard pdb.

If you don't want\can't use excepthook (usually other modules use the excepthook), you can use `atexit`:
```python
from ddebug import set_atexit
set_atexit()
```
### watch
`ddebug` has a `watch` and `unwatch` (named also `w` and `unw`) functions from [watchpoints](https://github.com/gaogaotiantian/watchpoints)
```python
from ddebug import dd
a = []
dd.watch(a)
a = {}
```
Output

```shell
====== Watchpoints Triggered ======
Call Stack (most recent call last):
  <module> :
>   a = {}
a:
[]
->
{}
```
### install()
To make dd available in every file (without needing to import ddebug) just use:
```python
from ddebug import dd
dd.install() # install only "dd" name
# you can chose an alias
dd.install(("dd","d"))
```

### Disabling
dd has an attribute named enabled. Set to false to suppress output.
```python
from ddebug import dd
dd(12) # ic 12
dd.enabled = False
dd(12) # not ic anything
```
This disabes `@dd`,`dd()`,`dd.<un>watch` and `dd.mincls`
For disabling the excepthook do:
```python
import sys
sys.excepthook = sys.__excepthook__
```
or comment out the call to set_excepthook().
### Operations
dd has a lot of operations that are equal to `dd(a)`:
```python
from ddebug import dd
a = "a"
b = dd+a
b = dd*a
b = dd@a
b = dd>>a
b = dd<<a
b = a|dd
b = dd|a
b = dd&a
```
Don't use `<>=`(e.g. `+=`) operations. icecream can't get source code and throws a ScoreError.
### Streams
if you want to write to tmp file (like [q](https://github.com/zestyping/q)) and also to stderr just do:
```python
dd.add_tmp_stream()
```
If you want only a tmp file(without stderr):
```python
dd.add_tmp_stream(with_print=False)
```
if you want to write only to custom file do:
```python
with open("output.txt") as output:
  dd.stream = output
```
All of them will remove color form stderr print.

All of them will affect:`@dd`,`dd()` and `dd.mincls` but not `dd.<un>watch`.

### ddebug as cli
You can run the entire file with snoop (like [futurecoder](https://futurecoder.io/)) and with dd.excepthook by simply typing:
```shell
python -m ddebug <file.py>
```
### Short dd name
You can do `from ddebug import dd as d`

### Dependencies
dd depends on the python librarys:
* [snoop](https://github.com/alexmojaki/snoop) - main dependency
* [icecream](https://github.com/gruns/icecream) - main dependency
* [watchpoints](https://github.com/gaogaotiantian/watchpoints) - for `dd.watch` and `dd.unwatch`
* [inputimeout](https://pypi.org/project/inputimeout) - for ask to start pdb debugger (in excepthook)
* [friendly_traceback](https://github.com/aroberge/friendly-traceback) - for create and print the friendly-traceback in excepthook
* [stackprinter](https://github.com/cknd/stackprinter) - for create stackprinter.txt (in excepthook)
* [better_exceptions](https://github.com/Qix-/better-exceptions) - for create better_exceptions.txt (in excepthook)
* [click](https://click.palletsprojects.com/) - for cli in `python -m ddebug`

### Contribute
On all errors, problems or suggestions please open a [github issue](https://github.com/matan-h/ddebug/issues)
