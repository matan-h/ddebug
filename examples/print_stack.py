from ddebug.dd_class import dd


def a():
    b()


def b():
    c()


def c():
    h()


def h():
    dd.print_stack()


def main():
    a()


if __name__ == '__main__':
    main()
