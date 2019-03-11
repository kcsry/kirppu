# -*- coding: utf-8 -*-

import argparse
import ast
import functools
import os.path

try:
    from typing import List
except ImportError:
    class _AbstractType(object):
        def __getitem__(self, item):
            pass
    List = _AbstractType()


__author__ = 'codez'


class Arg(object):
    def __init__(self, name):
        self.name = name
        self.optional = False


class Writer(object):
    def __init__(self, output):
        self._output = output
        self.print = functools.partial(print, file=self._output)

    def write_stub_header(self):
        pass

    def write_source_file_header(self, file: str):
        pass

    def write_function(self, module: str, node: ast.FunctionDef, arguments: List[Arg]):
        pass

    def write_source_file_trailer(self):
        pass

    def write_stub_trailer(self):
        pass


class JsWriter(Writer):
    def write_stub_header(self):
        self.print("""throw "Don't use";  // Automatically generated with make_api_stub""")
        self.print("// noinspection UnreachableCodeJS,JSUnusedGlobalSymbols")
        self.print("Api = {")

    def write_source_file_header(self, file: str):
        self.print("    // region", file)
        self.print()

    def write_function(self, module: str, node: ast.FunctionDef, arguments: List[Arg]):
        has_args = False
        for index, arg in enumerate(arguments):
            if index == 0 and arg.name == "request":
                continue
            if index == 1:
                self.print("    /** @param {Object} obj Parameters")
                has_args = True
            else:
                self.print()

            if arg.optional:
                self.print("     *  @param [obj.{name}]".format(name=arg.name), end="")
            else:
                self.print("     *  @param obj.{name}".format(name=arg.name), end="")

        if has_args:
            self.print("    */")
        self.print("    {name}: function({obj}) {{ /**".format(name=node.name, obj="obj" if has_args else ""))
        self.print("        {module}.{name}".format(module=module, name=node.name))
        self.print("    */},")
        self.print()

    def write_source_file_trailer(self):
        self.print("    // endregion")
        self.print()

    def write_stub_trailer(self):
        self.print("};")


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
    def __init__(self, mod: str, file: str, writer: Writer):
        self._decorator_visitor = DecoratorCallVisitor()
        self._module = mod
        self._file = file
        self._header_written = False
        self._writer = writer

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
            self._writer.write_source_file_header(self._file)

        if node.args:
            arguments = self.parse_arguments(node.args)
        else:
            arguments = []
        self._writer.write_function(self._module, node, arguments)

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
            self._writer.write_source_file_trailer()


def handle_source(f: str, writer: Writer):
    with open(f, "rt") as handle:
        tree = ast.parse(handle.read(), f)
        mod = os.path.splitext(os.path.basename(f))[0]
        visitor = MainVisitor(mod, f, writer)
        visitor.visit(tree)
        visitor.end()


def handle_sources(sources: List[str], writer: Writer):
    writer.write_stub_header()
    for f in sources:
        handle_source(f, writer)
    writer.write_stub_trailer()


def main(args=None):
    parser = argparse.ArgumentParser(description="Create API stub file(s).")
    parser.add_argument("--js", type=str, action="append", help="JavaScript stub file to write into.")
    parser.add_argument("source", type=str, nargs="+", help="Python source file.")

    arguments = parser.parse_args(args)

    for filename in arguments.js:
        with open(filename, "wt") as f:
            writer = JsWriter(f)
            handle_sources(arguments.source, writer)


if __name__ == "__main__":
    main()
