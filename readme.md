# ddebug
ddebug is a python library with a set of tools for simple debugging of python progams. It works only within a python file, not in the console.

ddebug is both
[icecream](https://github.com/gruns/icecream),
[snoop](https://github.com/alexmojaki/snoop) and [rich](https://github.com/willmcgugan/rich).

ddebug works with python 3.6+.

## Installation
Install using pip: ```(python -m) pip install ddebug```


## Simple Example
```python
from ddebug import dd
@dd  # do @snoop on a function
def foo(n):
    return n + 333
@dd  # do @snoop on all class functions (only possible in ddebug)
class A:
    def bar(self, n):
        return n + 333

dd(A().bar(foo(123)))  # use like icecream.
```
output:
```shell
12:00:00.00 >>> Call to foo in File "python file.py", line 3
12:00:00.00 ...... n = 123
12:00:00.00    3 | def foo(n):
12:00:00.00    4 |     return n + 333
12:00:00.00 <<< Return value from foo: 456
12:00:00.00 >>> Call to A.bar in File "python file.py", line 7
12:00:00.00 .......... self = <__main__.A object at 0x04F64E80>
12:00:00.00 .......... n = 456
12:00:00.00    7 |     def bar(self, n):
12:00:00.00    8 |         return n + 333
12:00:00.00 <<< Return value from A.bar: 789
dd| A().bar(foo(123)): 789
```
## Tracebacks
In `ddebug` there is an option for more detailed (and more beautiful) traceback than the regular traceback:

```python
from ddebug import dd
#place at start of program
dd.set_excepthook()
```
Then when an error occurrs `ddebug` creates a file named `<file>-errors.txt`:
the file starts with [rich](https://github.com/willmcgugan/rich) (render Python tracebacks with syntax highlighting and formatting)
and then  [friendly](https://github.com/aroberge/friendly) explanation of the error.

and ddebug will print all this file in colors.

In addition, you can press Enter within the first 5 seconds after exception and it will open the
[pdbr debugger](https://github.com/cansarigol/pdbr).
if pdbr has a error, ddebug will start standard pdb.

![ddebug traceback image](https://github.com/matan-h/ddebug/blob/master/images/traceback.png?raw=true)

If you don't want\\can't use excepthook (because usually other modules use the excepthook), you can use `atexit`:
```python
from ddebug import dd
dd.set_atexit()
```
if you want to choose file name:
pass `file=<file>` to the function.

if you want ddebug only print to console (without file):
pass `with_file=False` to the function.

you can control ddebug usage of pdbr debugger automatically with system variable `ddebug_pdb`:
set `ddebug_pdb=1` to set the input always to True
set `ddebug_pdb=0` to set the input always to False
set `ddebug_pdb=None` or delete `ddebug_pdb` to not set the input

## More options
### print stack
ddebug has a beautiful debug tool for print stack (to see the current stack without raising an error):

![ddebug print_stack image](https://github.com/matan-h/ddebug/blob/master/images/print_stack.png?raw=true)

just do:
```python
from ddebug import dd
#  print stack like traceback
dd.print_stack()
# print stack like traceback only last 3 calls
dd.print_stack(block=3)
```
### print_exception
you can also use [ddebug traceback](#Tracebacks) (without pdbr and the files) in try/except:
```python
from ddebug import dd
try:
    1/0
except Exception:
    dd.print_exception()
```
ddebug also has shortcut for this using `log_error` (named also except_error):
```python
with dd.log_error():
    1/0
```
or in function:
```python
@dd.log_error_function # named also except_error_function
def test():
    return 1/0
dd.print_exception()
```

### watch
`ddebug` has a `watch` and `unwatch` (named also `w` and `unw`) using [watchpoints](https://github.com/gaogaotiantian/watchpoints).
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

By default all of this output is printed to `sys.stderr`.
If you want to change this, do:

```python
from ddebug import dd
import sys
dd.watch_stream = sys.stdout # or another file/stream as you want
```
### snoop common arguments
You can [config snoop common arguments](https://github.com/alexmojaki/snoop#common-arguments) with  `dd.snoop_short_config` (named also ssc) with:
```python
from ddebug import dd
dd.snoop_short_config(watch=('foo.bar', 'self.x["whatever"]'),watch_explode=['foo', 'self'])
@dd.ssc(watch=('foo.bar', 'self.x["whatever"]'))   # you even use that as the @dd
def foo(n):
  return n+333
foo(123)
  ```
### diff
ddebug can show difference bitween two objects using [deepdiff](https://github.com/seperman/deepdiff) (ddebug also formats this using rich):

![ddebug difference image](https://github.com/matan-h/ddebug/blob/master/images/diff.png?raw=true)

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
### locals
ddebug can print all locals in colors by the command:
```python
from ddebug import dd
a = "ddebug"
b = "-"
c = "locals"
dd.locals()
```
### Concatenating
If you use ddebug as a function like icecream, e.g. `dd(value)` it will return the arguments you passed in to it:
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
This disabes all ddebug tools except for the dd-tracebacks.

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
All of them will remove color from stderr print.

All of them will affect all ddebug tools except the Tracebacks.

### Output folder
If you want to see all the output of ddebug in one folder you can do:
```python
from ddebug import dd
dd.add_output_folder()  # then all output goes to folder and stderr - it will also remove color.
```
it will create a folder named `<file>_log` and create 4 .txt files:
* `watch-log` - output from `dd.<un>watch`
* `snoop-log` - output from `@dd` on class or function and from `dd.deep`
* `icecream-log` - output from `dd()` and `@dd.mincls`.
* `rich-log` - output from `dd.pprint`,`dd.inspect`,`dd.diff` and `dd.print_stack()`

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

 config `icecream.includeContext` (dd() calls filename, line number, and parent function to dd output.) by:`dd.icecream_includeContext = True`.

 config [`friendly.language`](https://aroberge.github.io/friendly-traceback-docs/docs/html/usage_adv.html#language-used) by `dd.friendly_lang = "<languages>"`

 config [`rich color-system`](https://rich.readthedocs.io/en/stable/console.html#color-systems) by: `dd.rich_color_system = <color-system>`

## with dd
`with dd` equal to [`with snoop`](https://github.com/alexmojaki/snoop#basic-snoop-usage).

## more debbug tools:
### inspect()
`dd.inspect(obj)` equal to [`rich.inspect`](https://github.com/willmcgugan/rich#rich-inspect)

### pprint()
`dd.pprint` wiil pretty print the variable using rich

### deep()
`dd.deep` equal to [`snoop.pp.deep`](https://github.com/alexmojaki/snoop#ppdeep-for-tracing-subexpressions)


## Dependencies
ddebug depends on the python librarys:
* [snoop](https://github.com/alexmojaki/snoop) - main dependency
* [rich](https://github.com/willmcgugan/rich) -  main dependency
* [icecream](https://github.com/gruns/icecream) - main dependency
* [friendly](https://github.com/aroberge/friendly) - for explanation on the error in Tracebecks
* [pdbr](https://github.com/cansarigol/pdbr) - for make the pdb more colorful.
* [inputimeout](https://pypi.org/project/inputimeout) - for ask to start pdbr debugger in Tracebecks
* [watchpoints](https://github.com/gaogaotiantian/watchpoints) - for `dd.watch` and `dd.unwatch`
* [deepdiff](https://github.com/seperman/deepdiff) - for `dd.diff`

## Contribute
On all errors, problems or suggestions please open a [github issue](https://github.com/matan-h/ddebug/issues)  

If you found this library useful, it would be great if you could buy me a coffee:  

<a href="https://www.buymeacoffee.com/matanh" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/default-blue.png" alt="Buy Me A Coffee" height="47" width="200"></a>
