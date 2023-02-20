from pprint import pprint
from colorama import Fore
from typing import Any
from dataclasses import dataclass

try:
    import abstract_syntax_tree as AST
except ImportError:
    from . import abstract_syntax_tree as AST

@dataclass
class Free:
    value: Any
    lineno: int

class ASTAnalyzer:
    def __init__(self, filename, ast, string=""):
        self.filename = filename
        self.ast = ast
        self.code = string

        if not string:
            with open(filename, "r") as f:
                self.code = f.read()
                f.close()

        self.typetable = {
            "isize": AST.Integer,
            "usize": AST.Integer,
            "i32": AST.Integer,
            "u32": AST.Integer,
            "i16": AST.Integer,
            "u16": AST.Integer,
            "i8": AST.Integer,
            "u8": AST.Integer,
            "string": AST.String
        }

        self.variable_table = {}

    def __get_line(self, ln):
        if self.filename == "<stdio>":
            data = self.code.split("\n")

            if ln > len(data):
                return None

            return data[ln - 1]

    def fatal_error(self, op, message, note=None, fixcode=None):
        print(Fore.LIGHTRED_EX + "error: " + Fore.RESET + \
              f"(at {self.filename}:{op.lineno}): " + \
              message)
        print(" "*8 + f"{Fore.MAGENTA}{op.lineno}{Fore.RESET} | " + self.__get_line(op.lineno))
        if note:
            print(Fore.LIGHTCYAN_EX + "note: " + Fore.RESET + note)
        if fixcode:
            print(" "*8 + f"{Fore.MAGENTA}{op.lineno}{Fore.RESET} |  " + fixcode)
        exit(1)

    def warn(self, op, message, note=None, fixcode=None):
        print(Fore.LIGHTYELLOW_EX + "warning: " + Fore.RESET + \
              f"(at {self.filename}:{op.lineno}): " + \
              message)
        print(" "*8 + f"{op.lineno} | " + self.__get_line(op.lineno))
        if note:
            print(Fore.LIGHTCYAN_EX + "note: " + Fore.RESET + note)
        if fixcode:
            print(" "*8 + f"{op.lineno} |  " + fixcode)

    def suggest_code_init_var_type(self, name, value):
        typ = None
        
        if type(value) is AST.Integer:
            if value.value < 0: typ = "i32"
            else: typ = "u32"
        elif type(value) is AST.String:
            typ = "string"
        else:
            return None

        return Fore.LIGHTGREEN_EX + typ + Fore.RESET + \
               " " + name + " = " + str(value.value) + ";"

    def get_var(self, op, name, err=True):
        if name not in self.variable_table:
            if err:
                self.fatal_error(op, f"Variable `{name}` is not found!",
                           "Define and initialize it first.")
            else:
                return None
        else:
            return self.variable_table[name]

    def resolve_binop_type(self, binop, parent=None):
        if type(binop) is not AST.BinOp: return binop
        # Extract
        bl = binop.left
        br = binop.right
        # print("Got:", type(bl), type(br))

        # Evaluate inner binops
        if type(bl) is AST.BinOp:
            bl = self.resolve_binop_type(bl, binop)
        elif type(bl) is AST.Name:
            bl = self.resolve_binop_type(self.get_var(parent, bl.value).value, binop)
        
        if type(br) is AST.BinOp:
            br = self.resolve_binop_type(br, binop)
        elif type(br) is AST.Name:
            br = self.resolve_binop_type(self.get_var(parent, br.value).value, binop)

        # Lead to one type
        if type(bl) is type(br):
            # print("Resolved:", type(bl), type(br), "=>", type(bl))
            return bl
        else:
            typenamel = type(bl).__name__
            typenamer = type(br).__name__
            self.fatal_error(
                parent,
                f"An attempt to evaluate binary operation with two unsupported types: ({typenamel} and {typenamer})"
            )
            exit(1)
        return binop

    def analyze_part(self, op):
        t = type(op)
        if t is AST.End and op.char == ";":
            self.warn(op, "Redundant character `;` (creates a unnecessary operation).",
                 "Remove it.")
        elif t is AST.Assignment:
            nametype = type(op.name)
            name = op.name.value if nametype is AST.Name else op.name.var.value
            type_str = op.name.type.value
            # Variable exists?
            if nametype is not AST.TypedVarDefinition and op.name.value not in self.variable_table:
                self.fatal_error(op, f"Variable `{op.name.value}` is not found!",
                           "Define and initialize it first.",
                           self.suggest_code_init_var_type(op.name.value, op.value))
            # Variable of another type
            # TODO: Resolve BinOp
            if nametype is AST.TypedVarDefinition:
                if type_str in self.typetable:
                    if type(self.resolve_binop_type(op.value, op.value)) is not self.typetable[type_str]:
                        self.fatal_error(
                            op,
                            f"An attempt to assign value of another type than declared in variable!" + \
                            f" (`{self.resolve_binop_type(op.value)}` vs `{type_str}`)",
                            "Check and fix type.",
                            type(self.suggest_code_init_var_type(name, op.value))
                        )
            # OK
            self.variable_table[name] = op

            pprint(("Variable table:", self.variable_table))
        elif t is AST.Func:
            # TODO: Some checks...

            if op.name.value == "main" and not op.ret:
                # If user not specified return type for main function, do it instead
                # to prevent c compiler warning
                # -1 is no value and I hope it don't be detected by an analyzer
                op.ret = AST.Name("isize", -1, -1)
                op.code.operations.append(
                    AST.Operation(
                        AST.Return(
                            AST.Integer(
                                0, -1, -1
                            ), -1
                        ),
                    -1)
                )
        return op

    def __resolve_assign_name(self, name):
        if type(name) is AST.TypedVarDefinition:
            return name.var.value
        else:
            return name.value

    def _mini_eval(self, op):
        t = type(op)
        if t is AST.TypedVarDefinition:
            return op.var.value
        elif t is AST.Integer:
            return op.value
        elif t is AST.Name:
            return op.value
        elif t is AST.String:
            return op.value

    def analyze_memory(self, ops, func=None, funcs={}):
        allocs = {}

        for n, i in enumerate(ops):
            op = i.op

            if type(op) is AST.Assignment:
                if type(op.value) is AST.New:
                    allocs[self.__resolve_assign_name(op.name)] = op.value
                    print(self.__resolve_assign_name(op.name), "=", op.value)
                elif type(op.value) is AST.FunctionCall:
                    if funcs[op.value.name.value].need_dealloc:
                        allocs[self.__resolve_assign_name(op.name)] = op.value
                        print(self.__resolve_assign_name(op.name), "=", op.value)
            elif type(op) is AST.Func:
                # print(f"=== ENTERING TO {op.name.value} ===")
                funcs[op.name.value] = op
                op.code.operations = self.analyze_memory(op.code.operations, op, funcs)
            elif type(op) is AST.Return:
                print(op)
                if func and (self._mini_eval(op) in allocs):
                    func.need_dealloc = True

                if op.value.value in allocs:
                    del allocs[op.value.value]

                ops = ops[:n-1] + \
                      [AST.Operation(Free(i, allocs[i].lineno), allocs[i].lineno) for i in allocs.keys()] + \
                      ops[n:]  # Free memory before return
                return ops
            else:
                print("Unsupported:", type(op).__name__)

        ops.extend([AST.Operation(Free(i, allocs[i].lineno), allocs[i].lineno) for i in allocs.keys()])

        return ops
        exit(1)

    def analyze(self):
        for n, i in enumerate(self.ast.operations):
            self.ast.operations[n].op = self.analyze_part(i.op)

        self.analyze_memory(self.ast.operations)
        
        return self.ast
