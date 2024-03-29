from colorama import Fore
from pprint import pprint
from typing import Any
from dataclasses import dataclass

try:
    import abstract_syntax_tree as AST
except ImportError:
    from . import abstract_syntax_tree as AST

# TODO/FIXME: Add support to check structs and class of DIFFERENT types
#             
#             Example:
#                  func test(mystruct1 a) { ... }
#
#                  func main() {
#                      mystruct2 lalala = new mystruct2;
#
#                      test(lalala)  // Error, could not pass mystruct2 as parameter of mystruct1
#                  }

@dataclass
class Free:
    """
    That class indicates a allocated value to be freed
    """
    value: Any
    lineno: int

class ASTAnalyzer:
    def __init__(self, filename, ast, string=""):
        """
        Initializer of the Analyzer

        Analyzer does some things like:
        - Type checking
        - Variable and function existance
        - Warn if needed
        """
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
        """
        Get line of code we loaded
        """
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
        """
        Suggests a fixed line of code for variable mistyping
        """
        typ = None

        # If value is integer
        if type(value) is AST.Integer:
            # Detect signed or unsigned
            if value.value < 0: typ = "i32"
            else: typ = "u32"
        # Or string?
        elif type(value) is AST.String:
            typ = "string"
        # Huh?
        else:
            return None

        # Mark suggested type green
        return Fore.LIGHTGREEN_EX + typ + Fore.RESET + \
               " " + name + " = " + str(value.value) + ";"

    def get_var(self, op, name, err=True):
        """
        Gets a variables

        If error occured, show error and exit
        """
        if name not in self.variable_table:
            if err:
                self.fatal_error(op, f"Variable `{name}` is not found!",
                           "Define and initialize it first.")
            else:
                return None
        else:
            return self.variable_table[name]

    def get_funcs(self, funcname: str) -> list:
        """
        Get all functions with {funcname}
        """
        return [i for i in self.func_table if i.name.value == funcname]

    def get_return_type_of_funccall(self, funccall: AST.FunctionCall):
        """
        Get return type of function that function call refers to
        """
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

    def get_type(self, op, typename: str):
        """
        Gets a internal type that typename refers to
        """
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
        if not args: return []
        curtype = args[0].type
        array = args[0].array
        total = []

        for i in args:
            if type(i) is AST.TypedVarDefinition:
                curtype = i.type
                array = i.array
                total.append(i)
            else:
                total.append(
                    AST.TypedVarDefinition(
                        curtype,
                        array,
                        i,
                        i.lineno
                    )
                )
        return total

    def find_matching_arguments(self, funcname: str, call: AST.FunctionCall):
        """
        Finds matching function by its arguments
        Returns a function, that matchees by all {input_arguments}
        """

        # Get all function of this name
        funcs = self.get_funcs(funcname)

        # If no funcs
        if len(funcs) == 0:
            self.fatal_error(
                call, f"Function `{funcname}` not found!"
            )

        # Unpack arguments and save it in list
        argument_list_for_every_func = [i.args.value for i in funcs]
        argument_list_for_every_func = [self.unpack_func_args(i) for i in argument_list_for_every_func]

        # Convert arguments to types
        argument_types_for_every_func = [
            [self.get_type(funcs[n], j.type.value) for j in i]
            for n, i in enumerate(argument_list_for_every_func)
        ]

        # Convert FuncCall arguments to types too
        call_args = call.arguments.value
        call_args_types = [self.resolve_binop_type(i, i) for i in call_args]

        # Go through all arguments of function (not call)
        for n, i in enumerate(argument_types_for_every_func):
            # If length matches...
            if len(i) == len(call_args_types) \
               and all([i[w] is j for w, j in enumerate(call_args_types)]):
                # Set origin of this function
                # FIXME: Make origin detection in separate function (Recursively)
                call.origin = funcs[n]
                # Return it
                return funcs[n]

        # FIXME: Remake it to real error ↓↓↓

        # Debug information
        print(f"No one function call arguments for `{funcname}` was found!")
        print(f"Debug: total found: {len(argument_types_for_every_func)} funcs with the same name")
        print()
        print(f"Call is: {funcname}({[i.__name__ for i in call_args_types]})")
        print()
        print("Available:")
        for i in argument_types_for_every_func:
            print(f"=> {funcname}({[j.__name__ for j in i]})")
        exit(1)

    def resolve_struct_endpoint_type(self, op: AST.Struct, path_elems: list):
        fields = self.unpack_func_args(op.value.value[0].value)

        for i in fields:
            if i.var.value == path_elems[0].value:
                return self.get_type(op, i.type.value)

        print("Debug: Field `{path_elems[0]}` not found in struct `{op.name.value}`")
        exit(1)

    def resolve_path_endpoint_type(self, op: AST.Path, path_elems: list):
        start = path_elems[0].value  # Name

        if start in self.variable_table:  # Is variable?
            var = self.variable_table[start]  # Get definiton to extract type
            orig = self.get_type(op, var.type.value)  # Get elements that variable refers to
            
            # print("Original struct")
            # pprint(orig)

            if type(orig) is AST.Struct:
                return self.resolve_struct_endpoint_type(orig, path_elems[1:])

    def resolve_binop_type(self, binop, parent=None):  # Returns a type
        """
        Tries to resolve what type object have.

        Example:
            struct abc { ... }  // => Struct (needs additional checking)
            4 + 8  // => BinOp(Integer + Integer) => Integer
            "Hello" + 3.14  // => !!! Error: cannot add float to string
        """
        # TODO: Do additional checking for structs

        # print("Got: ", end='')
        # pprint(binop)
        
        if type(binop) is AST.FunctionCall:  # Process a function call
            ret = self.get_return_type_of_funccall(binop)
            if not ret: return None
            # print("Evaluating call for: ", binop.name.value)
            self.find_matching_arguments(binop.name.value, binop)
            return self.typetable[self._mini_eval(ret)]

        if type(binop) is AST.Name:
            var = self.get_var(parent, binop.value)
            # print(" VAR IS ", var)
            # return self.resolve_binop_type(var.value if type(var) is AST.Name else var.type.value, binop)
            return self.get_type(binop, var.type.value) # if type(var) is AST.Name else var.type.value

        if type(binop) is AST.Path:
            return self.resolve_path_endpoint_type(binop, binop.elements)

        if type(binop) is AST.New:
            if type(binop.obj) is AST.Indexed:
                return self.get_type(binop, binop.obj.var.value)
            return self.get_type(binop, binop.obj.value)

        if type(binop) is AST.Indexed:
            print("indexed!")

            vname = binop.var.value
            typename = self.get_var(binop, vname).type.value

            return self.get_type(binop, typename)

        if type(binop) is not AST.BinOp: return type(binop)
        # Extract
        bl = binop.left
        br = binop.right
        # print("Got:", type(bl), type(br))`

        # Evaluate inner binops
        if type(bl) is AST.BinOp:
            bl = self.resolve_binop_type(bl, binop)
        elif type(bl) is AST.Name:
            var = self.get_var(parent, bl.value)
            typ = self.typetable[var.type.value]
            # print(typ)
            # bl = self.resolve_binop_type(var.value, binop)
            bl = typ

        if type(bl) is AST.FunctionCall:
            self.find_matching_arguments(bl.name.value, bl)
        
        if type(br) is AST.BinOp:
            br = self.resolve_binop_type(br, binop)
        elif type(br) is AST.Name:
            var = self.get_var(parent, br.value)
            typ = self.typetable[var.type.value]
            # print(typ)
            # br = self.resolve_binop_type(var.value, binop)
            br = typ

        if type(br) is AST.FunctionCall:
            self.find_matching_arguments(br.name.value, br)

        bl = type(bl) if type(bl) is not type else bl
        br = type(br) if type(br) is not type else br

        # Lead to one type
        if bl is br:
            print("Resolved:", bl, "/", br, "=>", bl)
            # return type(bl) # if type(bl) is not type else bl
            return bl
        else:
            typenamel = bl.__name__
            typenamer = br.__name__
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

            if type(op.name) is AST.ParameterList:
                print("TODO: Assignment on multiple variables in analyzer.py (:analyze_part)")
                # exit(1)
                return op
            name = op.name.value if nametype is AST.Name else op.name.var.value

            # Variable exists?
            if nametype is not AST.TypedVarDefinition and name not in self.variable_table:
                # TODO: Array support
                self.fatal_error(op, f"Variable `{name}` is not found!",
                           "Define and initialize it first.",
                           self.suggest_code_init_var_type(name, op.value))
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
                            "An attempt to assign value of another type than declared in variable!" + \
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

            args = self.unpack_func_args(op.args.value)
            argsvar = {}

            for i in args:
                argsvar[i.var.value] = i

            self.func_table.append(op)

            tmp = ASTAnalyzer(self.filename, op.code)
            tmp.variable_table = self.variable_table | argsvar
            tmp.func_table = self.func_table
            tmp.typetable = self.typetable
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
            # self.func_table.append(op)
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
            tmp.typetable = self.typetable
            # print(tmp.variable_table)

            # pprint(op)
            tmp.common_analyze(op.code.operations, loop=True)
        elif t is AST.While:
            tmp = ASTAnalyzer(self.filename, op.code)
            tmp.variable_table = self.variable_table
            tmp.func_table = self.func_table
            tmp.typetable = self.typetable
            tmp.common_analyze(op.code.operations, loop=True)
        elif t is AST.FunctionCall:
            self.find_matching_arguments(op.name.value, op)
        elif t is AST.IfElse:
            tmp = ASTAnalyzer(self.filename, op.code)
            tmp.variable_table = self.variable_table
            tmp.func_table = self.func_table
            tmp.typetable = self.typetable
            tmp.common_analyze(op.code.operations, loop=loop)

            tmp = ASTAnalyzer(self.filename, op.else_)
            tmp.variable_table = self.variable_table
            tmp.func_table = self.func_table
            tmp.typetable = self.typetable
            tmp.common_analyze(op.else_.operations, loop=loop)
        elif t is AST.Struct:
            sname = op.name.value
            self.typetable[sname] = op
        elif t is AST.Return:
            self.resolve_binop_type(op.value, op.value)
        return op

    def __resolve_assign_name(self, name):
        # FIXME: Remove this function, it's replaced by `_mini_eval()`
        if type(name) is AST.TypedVarDefinition:
            return name.var.value
        else:
            return name.value

    def _mini_eval(self, op):
        """
        Just get value from wrapper
        """
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
        """
        Analyze AST for memory allocations

        Add Free statement automatically when needed
        """
        allocs = {}

        # Go through all AST.Operations
        for n, i in enumerate(ops):
            op = i.op

            # If we assigned ...
            if type(op) is AST.Assignment:
                # ... allocation
                if type(op.value) is AST.New:
                    # Add its name to allocation list 
                    allocs[self.__resolve_assign_name(op.name)] = op.value
                # ... function call
                elif type(op.value) is AST.FunctionCall:
                    # ... that needs deallocation
                    if funcs[op.value.name.value].need_dealloc:
                        # Add its name to allocation list 
                        allocs[self.__resolve_assign_name(op.name)] = op.value
            # If we encountered func, analyze it, and add func's name to the list
            elif type(op) is AST.Func:
                funcs[op.name.value] = op
                op.code.operations = self.analyze_memory(op.code.operations, op, funcs)
            # If we encountered a return, check what kind of value function returns
            elif type(op) is AST.Return:
                # If we're scanning a function, and value is in list of allocated values
                # Mark function deallocateable
                if func and (self._mini_eval(op.value) in allocs):
                    func.need_dealloc = True

                # Evaluate a value's MAME that function returns
                val = self._mini_eval(op.value)

                # If we returning allocated value, do not free it
                if val and op.value.value in allocs:
                    del allocs[op.value.value]

                # Free all allocated values except returnable value
                ops = ops[:n] + \
                      [AST.Operation(Free(i, allocs[i].lineno), allocs[i].lineno) for i in allocs.keys()] + \
                      ops[n:]  # Free memory BEFORE return statement
                return ops
            else:
                # print("Unsupported:", type(op).__name__)
                ...

        # Free all allocated values in the function at the end
        ops.extend([AST.Operation(Free(i, allocs[i].lineno), allocs[i].lineno) for i in allocs.keys()])

        return ops

    def common_analyze(self, ops, loop=False, func=None):
        for n, i in enumerate(ops):
            self.ast.operations[n].op = self.analyze_part(i.op, loop=loop, func=func)

    def analyze(self):
        self.common_analyze(self.ast.operations)
        self.analyze_memory(self.ast.operations)
        
        return self.ast
