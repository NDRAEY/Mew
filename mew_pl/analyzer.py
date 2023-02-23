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
            "float": AST.Float,
            "double": AST.Float,
            "bool": AST.Bool,
            "string": AST.String
        }

        self.variable_table = {}
        self.func_table = []

    def __get_line(self, ln):
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
        print(" "*8 + f"{Fore.MAGENTA}{op.lineno}{Fore.RESET} | " + self.__get_line(op.lineno))
        if note:
            print(Fore.LIGHTCYAN_EX + "note: " + Fore.RESET + note)
        if fixcode:
            print(" "*8 + f"{Fore.MAGENTA}{op.lineno}{Fore.RESET} |  " + fixcode)

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

    def get_funcs(self, funcname: str) -> list:
        return [i for i in self.func_table if i.name.value == funcname]

    def get_return_type_of_funccall(self, funccall: AST.FunctionCall):
        funcname = funccall.name.value

        # TODO: Select function by input arguments (Done?)
        func = self.find_matching_arguments(funcname, funccall)

        """
        print("===Function call===")
        pprint(funccall.arguments)
        print("===Resolved===")
        pprint(func)
        """
    
        return func.ret

    def get_type(self, op, typename):
        if typename in self.typetable:
            return self.typetable[typename]
        else:
            self.fatal_error(
                op, f"Type `{typename}` is not found!"
            )
            ... # Error: Type {typename} is not found!

    def unpack_func_args(self, args):
        """
        Tries to unpack args like: type a, b, c
        To unpack them like: type a, type b, type c

        (But in AST style)
        """
        curtype = args[0].type
        total = []

        for i in args:
            if type(i) is AST.TypedVarDefinition:
                curtype = i.type
                total.append(i)
            else:
                total.append(
                    AST.TypedVarDefinition(
                        curtype,
                        i,
                        i.lineno
                    )
                )
        return total

    def find_matching_arguments(self, funcname: str, call: AST.FunctionCall):
        """
        Finds matching arguments for function {funcname}
        Returns a function, that matchees by all {input_arguments}
        """
        funcs = self.get_funcs(funcname)
        argument_list_for_every_func = [i.args.value for i in funcs]

        argument_list_for_every_func = [self.unpack_func_args(i) for i in argument_list_for_every_func]

        argument_types_for_every_func = [
            [self.get_type(funcs[n], j.type.value) for j in i]
            for n, i in enumerate(argument_list_for_every_func)
        ]

        call_args = call.arguments.value
        call_args_types = [type(i) for i in call_args]

        for n, i in enumerate(argument_types_for_every_func):
            if len(i) == len(call_args_types) \
               and all([i[w] is j for w, j in enumerate(call_args_types)]):
                return funcs[n]

        # FIXME: Remake it to real error ↓↓↓

        # Debug
        print(f"No one function call arguments for `{funcname}` was found!")
        exit(1)

    def resolve_binop_type(self, binop, parent=None):  # Returns a type
        # print("BINOP RESOLVER GOT: ", binop)

        if type(binop) is AST.FunctionCall:  # Process a function call too
            return self.typetable[self._mini_eval(self.get_return_type_of_funccall(binop))]

        if type(binop) is not AST.BinOp: return type(binop)
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
            print("Resolved:", type(bl), type(br), "=>", type(bl))
            return type(bl)
        else:
            typenamel = type(bl).__name__
            typenamer = type(br).__name__
            self.fatal_error(
                parent,
                f"An attempt to evaluate binary operation with two unsupported types: ({typenamel} and {typenamer})"
            )
            exit(1)
        return binop

    def analyze_part(self, op, loop=False, func=None):
        t = type(op)

        if t is AST.End and op.char == ";":
            self.warn(op, "Redundant character `;` (creates a unnecessary operation)",
                 "Remove it.")
        elif t is AST.Assignment:
            nametype = type(op.name)

            if nametype is AST.Path:
                print("FIXME: Analyze AST.Path when Assignment (analyzer.py)")
                return op
            
            name = op.name.value if nametype is AST.Name else op.name.var.value

            # Variable exists?
            if nametype is not AST.TypedVarDefinition and name not in self.variable_table:
                self.fatal_error(op, f"Variable `{op.name.value}` is not found!",
                           "Define and initialize it first.",
                           self.suggest_code_init_var_type(op.name.value, op.value))
            # print("Exists? > ", name in self.variable_table)

            if name not in self.variable_table:
                # print("Defining", name)
                self.variable_table[name] = op.name

            if type(op) is AST.TypedVarDefinition:
                type_str = op.name.type.value
            else:
                type_str = self.variable_table[name].type.value

            # Variable of another type
            if nametype is AST.TypedVarDefinition:
                # print("Definition")
                if type_str in self.typetable:
                    real_type = self.resolve_binop_type(op.value, op.value)
                    if real_type is not self.typetable[type_str]:
                        if real_type:
                            real_type = real_type.__name__.lower() + " (internal)"
                        self.fatal_error(
                            op,
                            f"An attempt to assign value of another type than declared in variable!" + \
                            f" (`{real_type or 'nothing'}` vs `{type_str}`)",
                            "Check and fix type.",
                            # type(self.suggest_code_init_var_type(name, op.value))
                            self.suggest_code_init_var_type(name, op.value)
                        )
                else:
                    # TODO: Add error, because type is not in Type Table indicates that type.is not defined!
                    ...
            # OK

            # pprint(("Variable table:", self.variable_table))
        elif t is AST.Func:
            # TODO: Some checks...

            tmp = ASTAnalyzer(self.filename, op.code)
            # print(tmp.variable_table)
            tmp.variable_table = self.variable_table
            tmp.func_table = self.func_table
            tmp.common_analyze(op.code.operations, func=t)

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

            # print("Added func:", op)
            self.func_table.append(op)
        elif t is AST.Warning:
            self.warn(op.refer, op.message)
            op = op.refer
        elif (t is AST.Break) and (not loop):
            self.fatal_error(op, "`break` statement not in loop")
        elif (t is AST.Continue) and (not loop):
            self.fatal_error(op, "`continue` statement not in loop")
        elif t is AST.Loop:
            # tmp = ASTAnalyzer(self.filename, AST.Program([op]))
            tmp = ASTAnalyzer(self.filename, op.code)
            tmp.variable_table = self.variable_table
            tmp.func_table = self.func_table
            # print(tmp.variable_table)

            # pprint(op)
            tmp.common_analyze(op.code.operations, loop=True)
        elif t is AST.While:
            tmp = ASTAnalyzer(self.filename, op.code)
            tmp.variable_table = self.variable_table
            tmp.func_table = self.func_table
            tmp.common_analyze(op.code.operations, loop=True)
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
                    # print(self.__resolve_assign_name(op.name), "=", op.value)
                elif type(op.value) is AST.FunctionCall:
                    if funcs[op.value.name.value].need_dealloc:
                        allocs[self.__resolve_assign_name(op.name)] = op.value
                        # print(self.__resolve_assign_name(op.name), "=", op.value)
            elif type(op) is AST.Func:
                # print(f"=== ENTERING TO {op.name.value} ===")
                funcs[op.name.value] = op
                op.code.operations = self.analyze_memory(op.code.operations, op, funcs)
            elif type(op) is AST.Return:
                if func and (self._mini_eval(op.value) in allocs):
                    func.need_dealloc = True

                val = self._mini_eval(op.value)

                if val and op.value.value in allocs:
                    del allocs[op.value.value]

                ops = ops[:n] + \
                      [AST.Operation(Free(i, allocs[i].lineno), allocs[i].lineno) for i in allocs.keys()] + \
                      ops[n:]  # Free memory before return
                return ops
            else:
                # print("Unsupported:", type(op).__name__)
                ...

        ops.extend([AST.Operation(Free(i, allocs[i].lineno), allocs[i].lineno) for i in allocs.keys()])

        return ops
        exit(1)

    def common_analyze(self, ops, loop=False, func=None):
        for n, i in enumerate(ops):
            self.ast.operations[n].op = self.analyze_part(i.op, loop=loop, func=func)

    def analyze(self):
        self.common_analyze(self.ast.operations)
        self.analyze_memory(self.ast.operations)
        
        return self.ast
