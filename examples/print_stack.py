import time
from ddebug.dd_class import *


def a():
    b()


def b():
    c()


def c():
    h()


def h():
    dd.except_error
def main():
    a()


if __name__ == '__main__':
    main()
