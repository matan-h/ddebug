# ddebug
ddebug Is python library for cool debugging python

ddebug is both
[icecream](https://github.com/gruns/icecream) and
[snoop](https://github.com/alexmojaki/snoop)
in simple and quick like [q](https://github.com/zestyping/q)
## Installation
Install using pip: ```(python -m) pip install ddebug```



## Simple Example 
```python
from ddebug import dd
@dd #can be snoop
def foo(n):
    return n+333
@dd # do @snoop on all class function
class A:
    def a(self):
        pass

dd(foo(123)) # can be icecream.
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

#### min cls:
sometimes you don't want to view all class-function process.you can use mincls option:
```python
from ddebug import dd
@dd.mincls
class A:
    def a(self):
        pass

a = A()
a.a()
a = "a"
b = "b"
dd(dd(a)+dd(b))
```
output:
```shell
dd| non.py:8 in <module>: call method 'a' from class 'A' at 11:34:15.383
dd| a: 'a'
dd| b: 'b'
dd| dd(a)+dd(b): 'ab'
```
#### tracebacks
```python
from ddebug import set_excepthook
set_excepthook()
```
then when error occurred ddebug create a folder named <file-errors>
and write 4 traceback files:
* print and write friendly_traceback.txt - [friendly_traceback](https://github.com/aroberge/friendly-traceback)
* write stackprinter.txt - [stackprinter](https://github.com/alexmojaki/stackprinter) 
* write better_exceptions.txt - [better_exceptions](https://github.com/Qix-/better-exceptions)
* traceback.txt - the normal traceback

sometimes you don't want\can to use excepthook.you can use atexit:
```python
from ddebug import set_atexit
set_atexit()
```
#### watch
dd has a `watch` and `unwatch` (named also `w` and `unw`) functions from [watchpoints](https://github.com/gaogaotiantian/watchpoints)
### install()
To make dd available in every file (without needing to import them) just use:
```python
from ddebug import dd
dd.install() # install only "dd" name
# you can chose names
dd.install(("dd","d"))
```
### Disabling
dd has an attr named enabled
```python
from ddebug import dd
dd(12) # ic 12
dd.enabled = False
dd(12) # not ic anything 
```
this is Disabling `@dd`,`dd()`,`dd.<un>watch` and `dd.mincls`
for Disabling the excepthook do:
```python
import sys
sys.excepthook = sys.__excepthook__
```
### operations
dd has a lot of operations that equal to `dd(a)`:
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
don't use `<>=`(e.g. `+=`) operations. icecream can't get source code and throw ScoreError.

