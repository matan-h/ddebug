# ddebug
ddebug is a python library for simple debugging of python progams. It works only within a python file, not in the console.

ddebug is both
[icecream](https://github.com/gruns/icecream) and
[snoop](https://github.com/alexmojaki/snoop)
but simple and quick to use in the style of [q](https://github.com/zestyping/q).

ddebug works with python 3.6+.

## Installation
Install using pip: ```(python -m) pip install ddebug```


## Simple Example
```python
from ddebug import dd
@dd #do @snoop on a function
def foo(n):
    return n+333
@dd # do @snoop on all class functions (only possible in ddebug)
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
## More options

### min cls:
Sometimes you don't want to view all the class functions internal processes, just see when it was called. Then you can use mincls(named also mc) option to just see the function call:
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
mincls does not yet support the __ <> __  functions(e.g. __ init __).

### Concatenating
If you use ddebug as a function like icecream, e.g. `dd(value)` it will returns the arguments you passed in to it:
```python
from ddebug import dd
a = "a"
b = "b"
c = dd(dd(a)+dd(b))
dd(c)
```
Output:
```shell
dd| a: 'a'
dd| b: 'b'
dd| dd(a)+dd(b): 'ab'
dd| c: 'ab'
```


### Tracebacks
In `ddebug` there is an option for more detailed traceback than the regular traceback:
```python
from ddebug import dd
#place at start of program
dd.set_excepthook()
```

Then when an error occurrs `ddebug` creates a file named `<file>-errors.txt`:
the file starts with [rich](https://github.com/willmcgugan/rich) (render Python tracebacks with syntax highlighting and formatting)
and then  [friendly](https://github.com/aroberge/friendly) explanation of the error.

In addition, you can press Enter within the first 5 seconds after exception and it will open the standard pdb.

If you don't want\can't use excepthook (because usually other modules use the excepthook), you can use `atexit`:
```python
from ddebug import dd
dd.set_atexit()
```
if you want to choose file name:
just pass `file=<file>` to the function.
### watch
`ddebug` has a `watch` and `unwatch` (named also `w` and `unw`) uses [watchpoints](https://github.com/gaogaotiantian/watchpoints).
```python
from ddebug import dd
a = []
dd.watch(a)
a = {}
```
Output

```shell
Watch trigger ::: File "python-file.py", line 4, in <module>
	a:was [] is now {}
```
By default all of this output is printed with the icecream printer.
If you want to change this, do:
```python
from ddebug import dd
import sys
dd.watch_stream = sys.stderr # or another file/stream as you want
```

### install()
To make dd available in every file (without needing to import ddebug) just write in the first file:
```python
from ddebug import dd
dd.install() # install only "dd" name
# you can chose an alias
dd.install(("dd","d"))
```

### Disabling
dd has an attribute named `enabled`. Set to false to suppress output.
```python
from ddebug import dd
dd(12) # will output ic(12)
dd.enabled = False
dd(12) # not output anything
```
This disabes `@dd`,`dd()`,`dd.<un>watch` and `dd.mincls`
For disabling the excepthook do:
```python
import sys
sys.excepthook = sys.__excepthook__
```
or comment out the call to `dd.set_excepthook()``.
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
for example: instead of trying to add `dd()` to `l = list(map(str,filter(bool,range(12))))`
you can do `l = dd @ list(map(str,filter(bool,range(12))))`

Don't use `<>=`(e.g. `+=`) operations. icecream can't get source code and will throw a ScoreError.
### print stack
if you want to see the current stack without raising an error do:
```python
from ddebug import dd
#  print sorted (from last frame to call of dd.print_stack()) stack (takes some time)
dd.print_stack()
# print stack (quick) like traceback
dd.print_stack(sort=False)
```

### Streams
If you want to write ddebug output to tmp file (like [q](https://github.com/zestyping/q)) and also to stderr just do:
```python
dd.add_tmp_stream()
```
If you want only a tmp file(without stderr):
```python
dd.add_tmp_stream(with_print=False)
```
if you want to write only to custom file do:
```python
dd.stream = open("output.txt","w")
```
**Don't forget to close the file.**
If you do not close the file - the file will probably not write.
My recommendation is to use built-in`atexit` module to close the file (you can use it even if you alredy use atexit (e.g. `dd.set_atexit()`):
```python
import atexit
from ddebug import dd
output_stream = open("output.txt", "w")
atexit.register(output_stream.close) #will close the file at the end of the program
dd.stream = output_stream
```
All of them will remove color form stderr print.

All of them will affect:`@dd`,`dd()`, `dd.mincls` and `dd.<un>watch`.

### Output folder
If you want to see all the output of ddebug in one folder you can do:
```python
from ddebug import dd
dd.add_output_folder()  # then all output goes to folder and stderr - it will also remove color.
```
it will create a folder named `<file>_log` and create 3 .txt files:
* `watch-log` - output from `dd.<un>watch`
* `snoop-log` - output from `@dd` on class or function
* `icecream-log` - output from `dd()`, `@dd.mincls` and `dd.print_stack()`

It will also set excepthook or atexit to create a file named `error.txt` in this folder.
Pass `with_errors=False` to this function to prevent this.

If you dont want each run of the program to overwrite the files in the folder or you want to see the date your script was run - do:
```python
dd.add_output_folder(with_date=True)
```
or:
```python
dd.add_output_folder(True)
```
There is way to choose folder name using a file:
```python
dd.add_output_folder(pyfile="python-file.py") # will create a folder python-file_log
```
or:
```python
dd.add_output_folder(folder="my-cool-folder") # will create a folder my-cool-folder
```
### config
You can [config snoop](https://github.com/alexmojaki/snoop#output-configuration) with:
`dd.snoopconfig(snoop-config-options)`.
All options but builtins and snoop names are valid.

You can config `icecream.includeContext` (dd() calls filename, line number, and parent function to dd output.) by:`dd.icecream_includeContext = True`.

you can config [`friendly.language`](https://aroberge.github.io/friendly-traceback-docs/docs/html/usage_adv.html#language-used) by `dd.friendly_lang = "<languages>"`

## with dd
`with dd` equal to [`with snoop`](https://github.com/alexmojaki/snoop#basic-snoop-usage).

## inspect()
`dd.inspect(obj)` equal to `rich.inspect`[https://github.com/willmcgugan/rich#rich-inspect]

## Dependencies
ddebug depends on the python librarys:
* [icecream](https://github.com/gruns/icecream) - main dependency
* [snoop](https://github.com/alexmojaki/snoop) - main dependency
* [watchpoints](https://github.com/gaogaotiantian/watchpoints) - for `dd.watch` and `dd.unwatch`
* [inputimeout](https://pypi.org/project/inputimeout) - to ask to start pdb debugger in error hooks
* [friendly](https://github.com/aroberge/friendly) - for explanation on the error in error-hooks
* [rich](https://github.com/willmcgugan/rich) - to create the traceback before friendly-traceback in error hooks and for `dd.inspect` function

## Contribute
On all errors, problems or suggestions please open a [github issue](https://github.com/matan-h/ddebug/issues)

<a href="https://www.buymeacoffee.com/matanh" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/default-blue.png" alt="Buy Me A Coffee" height="47" width="200"></a>
