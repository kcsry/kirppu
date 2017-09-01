# -*- coding: utf-8 -*-

import ast
import os.path
import sys

try:
    from typing import List
except ImportError:
    class _AbstractType(object):
        def __getitem__(self, item): pass
    List = _AbstractType()


__author__ = 'codez'


class Arg(object):
    def __init__(self, name):
        self.name = name
        self.optional = False


# noinspection PyPep8Naming
class DecoratorCallVisitor(ast.NodeVisitor):
    def visit_Call(self, node: ast.Call) -> bool:
        return self.visit(node.func)

    def visit_Attribute(self, node: ast.Attribute):
        return self.match_name(node.attr)

    def visit_Name(self, node: ast.Name):
        return self.match_name(node.id)

    @staticmethod
    def match_name(name):
        return name == "ajax_func"


# noinspection PyPep8Naming
class MainVisitor(ast.NodeVisitor):
    def __init__(self, mod: str, file: str):
        self._decorator_visitor = DecoratorCallVisitor()
        self._module = mod
        self._file = file
        self._header_written = False

    def visit_FunctionDef(self, node: ast.FunctionDef):
        if node.decorator_list:
            for decorator in node.decorator_list:
                if self._decorator_visitor.visit(decorator):
                    break
            else:
                return
        else:
            return

        if not self._header_written:
            self._header_written = True
            print("    // region {file} ".format(file=self._file))
            print()

        has_args = False
        if node.args:
            for index, arg in enumerate(self.parse_arguments(node.args)):
                if index == 0 and arg.name == "request":
                    continue
                if index == 1:
                    print("    /** @param {Object} obj Parameters")
                    has_args = True
                else:
                    print()

                if arg.optional:
                    print("     *  @param [obj.{name}]".format(name=arg.name), end="")
                else:
                    print("     *  @param obj.{name}".format(name=arg.name), end="")

            if has_args:
                print("    */")
        print("    {name}: function({obj}) {{ /**".format(name=node.name, obj="obj" if has_args else ""))
        print("        {module}.{name}".format(module=self._module, name=node.name))
        print("    */},")
        print()

    @staticmethod
    def parse_arguments(node: ast.arguments) -> List[Arg]:
        args = []  # type: List[Arg]
        for arg in node.args:
            args.append(Arg(arg.arg))

        for index, default in enumerate(node.defaults):
            args[-len(node.defaults) + index].optional = True

        return args

    def end(self):
        if self._header_written:
            print("    // endregion")
            print()


def main(args):
    if len(args) == 0:
        print("{}: should have python source files as arguments".format(sys.argv[0]), file=sys.stderr)
        exit(1)
    if args[0] == "--help":
        print("usage: {} file1.py [file2.py [... fileN.py]]".format(sys.argv[0]), file=sys.stderr)
        print("Outputs api_stub.js contents to stdout.", file=sys.stderr)
        exit(1)

    print("""throw "Don't use";  // Automatically generated with make_api_stub""")
    print("Api = {")

    for f in args:
        with open(f, "r") as handle:
            tree = ast.parse(handle.read(), f)
            mod = os.path.splitext(os.path.basename(f))[0]
            visitor = MainVisitor(mod, f)
            visitor.visit(tree)
            visitor.end()

    print("};")


if __name__ == "__main__":
    main(sys.argv[1:])
