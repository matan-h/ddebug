from ddebug import dd
# place at start of program:
dd.set_excepthook()

def foo(a):
    a = a - 1
    print(10 / a)

def bar(a):
    foo(a / 20)

if __name__ == '__main__':
    bar(20)