try:
    import abstract_syntax_tree as AST
    from analyzer import Free
    import log
except ImportError:
    from . import abstract_syntax_tree as AST
    from .analyzer import Free
    from . import log

from colorama import Fore
from pprint import pprint
import os

class CodeBuilder:
    def __init__(self, filename, ast, target, string="", structs={},
                 func=None, funcs={}, vartable={}):
        """
        Initializer of Code Builder that builds code from AST

        @param filename - filename of source code (need for error reporting) <--\
        @param ast - AST of source code                                         |
        @param string - If we using stdio (not file), we should pass code here -/
        """
        self.ast = ast
        self.filename = filename
        self.target = target

        if string:
            self.incode = string
        else:
            with open(self.filename, "r") as f:
                self.incode = f.read()
                f.close()
    
        self.code = ""

        self.structs = structs
        self.func = func

        # FIXME: Contain funcs in list for handling
        # overloaded functions, else every 'new' function with the 
        # same name and different arguments will be overwritten over 
        # old record
        
        self.funcs = funcs
        self.vartable = vartable

        self.typesizes = {}

        for i in ('u', 'i'):
            for j in (8, 16, 32, 64, "size"):
                self.typesizes[i+str(j)] = j//8 if j != "size" else 4

    def __get_line(self, ln):
        data = self.incode.split("\n")
        if ln > len(data):
            return None
        return data[ln - 1]
        
    def fatal_error(self, op, message):
        print(Fore.LIGHTRED_EX + "error: " + Fore.RESET + \
              f"(at {self.filename}:{op.lineno}): " + \
              message)
        print(" "*8 + f"{Fore.MAGENTA}{op.lineno}{Fore.RESET} |  " + self.__get_line(op.lineno))
        exit(1)

    def __unimplemented(self, op, message):
        print(Fore.LIGHTYELLOW_EX + "IMPLEMENT ME: " + Fore.RESET + \
                      f"(at {self.filename}:{op.lineno}): " + \
                      message)
        print(" "*8 + f"{Fore.MAGENTA}{op.lineno}{Fore.RESET} |  " + self.__get_line(op.lineno)+"\n")

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
                        curtype, array, i, i.lineno
                    )
                )
        return total

    def args2unique_name(self, args):
        args = self.unpack_func_args(args.value)

        name = ""

        for i in args:
            name += i.type.value
        return name

    def eval_value(self, op):
        t = type(op)

        if t is AST.Name:
            return op.value
        elif t is AST.Integer:
            return str(op.value)
        elif t is AST.String:
            # if len(op.value.split("\n")) > 1:
            # return '\\\n'.join(op.value.split("\n"))
            return op.value
        elif t is AST.ParameterList:
            total = ""
            for n, i in enumerate(op.value):
                if n != len(op.value) - 1: 
                    total += self.eval_value(i) + ", "
                else:
                    total += self.eval_value(i)
            return total
        elif t is AST.FunctionCall:
            return self.eval_funccall(op)
        elif t is AST.Assignment:
            return self.eval_assignation(op)
        elif t is AST.BinOp:
            return self.eval_binop(op)
        elif t is AST.Func:
            return self.eval_func(op)
        elif t is AST.TypedVarDefinition:
            return self.eval_TVD(op)
        elif t is AST.Return:
            return "return " + self.eval_value(op.value) + ";"
        elif t is AST.IfElse:
            return self.eval_if(op)
        elif t is AST.Struct:
            return self.eval_struct(op)
        elif t is AST.StructFieldArray:
            return self.eval_sfa(op)
        elif t is AST.New:
            return self.eval_new(op)
        elif t is Free:
            return self.eval_free(op)
        elif t is AST.Path:
            return self.eval_path(op)
        elif t is AST.ExternC:
            return self.eval_extern(op)
        elif t is AST.Loop:
            return self.eval_loop(op)
        elif t is AST.While:
            return self.eval_while(op)
        elif t is AST.Break:
            return "break;\n"
        elif t is AST.Continue:
            return "continue;\n"
        elif t is AST.Float:
            return str(op.value)
        elif t is AST.Bool:
            return str(op.value).lower()
        elif t is AST.Increment:
            return self.eval_value(op.what) + "++"
        elif t is AST.Decrement:
            return self.eval_value(op.what) + "--"
        elif t is AST.Indexed:
            return self.eval_value(op.var) + f"[{self.eval_value(op.index.elements[0])}]"
        elif t is AST.Use:
            self.__unimplemented(op, "`use statement`")
            return ""
        elif t is AST.End:
            return ""
        else:
            self.fatal_error(op, f"(internal) Unknown operation: {t.__name__}")

    def eval_while(self, op: AST.While):
        cmp  = self.eval_value(op.comparison)
        code = CodeBuilder(self.filename, op.code, self.target,
                           self.incode, self.structs).start(False)
        return "while(" + cmp + ") {" + code + "}\n"

    def eval_loop(self, op: AST.Loop):
        code = CodeBuilder(self.filename, op.code, self.target,
                           self.incode, self.structs).start(False)
        return "while(1) {" + code + "}\n"

    def eval_extern(self, op: AST.ExternC):
        return "\n" + op.code + "\n"

    def eval_path(self, op: AST.Path, ptr=False):
        a = ""

        # print("first element is: ", op.elements[0])
        first = op.elements[0]
        if type(first) is AST.Name:
            first = self.eval_value(first)
            if first in self.vartable and self.vartable[first] in self.structs:
                ptr=True

        for i in op.elements:
            a += self.eval_value(i) + ("." if not ptr else "->")
        return a[:(-1 if not ptr else -2)]
        # exit(1)

    def eval_funccall(self, fc):
        """
        Build a function call
        """
        fname = self.eval_value(fc.name)  # Name
        origin = fc.origin  # Get function that call refers to.
        uniq = self.args2unique_name(origin.args)  # Convert arguments types to unique name (Overloading)
        
        return fname + uniq + f"_({self.eval_value(fc.arguments)})"

    def eval_free(self, op):
        """
        Build a C-like free universal function()
        """
        return f"__allocator_free({op.value});\n"

    def sizeof_type(self, typ):
        """
        Get size of type
        """
        if typ in self.typesizes:
            return self.typesizes[typ]

    def sizeof_struct(self, val):
        """
        Calculates a size of struct we created.

        (Why not just use `sizeof(x)`?) IDK.
        """
        # If we passed a name of structure, get it from list
        if type(val) is str:
            return self.structs[val]

        size = 0

        # Get first field and parse its type
        curtype = self.eval_value(val[0].value[0].type)

        # Iterate over all fields
        for i in val:
            # Over all fields that declared in list
            # Like a, b and c from `type a, b, c`
            for j in i.value:
                if type(j) is AST.TypedVarDefinition:
                    curtype = self.eval_value(j.type)
                size += self.sizeof_type(curtype)

        return size

    def eval_sfa(self, op):
        """
        Builds a "Struct field array", a list of fields of struct
        """
        val = op.value
        code = ""

        # Add C-like fields to code
        for i in val:
            code += self.eval_value(i) + ";\n"

        return code

    def eval_struct(self, stc: AST.Struct):
        """
        Builds a C-like struct
        """
        name = self.eval_value(stc.name)
        value = self.eval_value(stc.value)

        # Register struct's size in struct table
        if name not in self.structs:
            self.structs[name] = self.sizeof_struct(stc.value.value)

        # Build it!
        return "typedef struct " + name + " {\n" + value + "\n} " + name + ";\n\n"

    def eval_assignation(self, a: AST.Assignment):
        """
        Builds C-like assignation
        """
        code = "" 

        name = a.name
        val  = self.eval_value(a.value)

        # Check whether variable is a pointer
        # -> If we allocated memory for variable directly using New
        # -> Or if we assigned variable a function that returns a allocated value
        ispointer = ((type(a.value) is AST.New) \
                     or ((type(a.value) is AST.FunctionCall) \
                          and self.funcs[a.value.name.value].need_dealloc
                        )
                    )

        # Build it!
        if type(name) is AST.Path:
            return self.eval_path(name, True) + " = " + val + ";\n"
        elif type(name) is not AST.TypedVarDefinition:
            return self.eval_value(name) + " = " + val + ";\n"

        # If we defining a variable usibg "full" definition: type name = value;
        typ = self.eval_value(name.type)  # Type
        var = self.eval_value(name.var)   # Value

        # Build it!
        code += typ + ("*" if ispointer else "") + " " + var + " = " + val + ";\n"

        # Register a variable in variable table
        self.vartable[var] = typ

        # print(f"Assigned {var} = {typ}")

        return code

    def eval_binop(self, binop: AST.BinOp):
        """
        Builds C-like Binary Operations recursively
        """
        return  "(" + self.eval_value(binop.left) + \
                " " + binop.op + " " + \
                self.eval_value(binop.right) + ")"

    def eval_TVD(self, tvd: AST.TypedVarDefinition):
        """
        Builds a variable definition.
        """
        code = ""

        typ = self.eval_value(tvd.type)  # Get type of variable
        var = tvd.var  # Get name of variable

        # If we defining one variable variable, just define it.
        if type(var) is not list:
            return typ + " " + self.eval_value(var)

        # If we defining TWO OR MORE variables, define them
        # TODO: Rewrite this
        for n, i in enumerate(var):
            if n != len(var)-1:
                code += typ + " " + self.eval_value(i) + ", "
            else:
                code += typ + " " + self.eval_value(i)
        return code

    def to_infunc_args(self, args):
        """
        Convert Mew's function arguments(parameters) to C-like arguments
        """
        # TODO: Because now we have a `unpack_func_args` function,
        # TODO: This function can be optimized
        
        code = ""  # Our future code
        args = args.value  # Values
        
        if len(args) == 0: return code  # If no arguments, return empty arguments

        # Because, we ALWAYS have a type (TypedVarDefinition) in first argument, use it
        curtype = self.eval_value(args[0].type)

        for n, i in enumerate(args):  # Iterate over all arguments
            # This `if` block checks, should we put comma at end or not
            # Except last argument, it doesn't needs a comma at end.
            
            # NOTE: It can be optimized!
            # NOTE: Like this:

            #       comma = ", " if (n != len(args)-1) else ""   # Here
            #       ...
            #       code += curtype + " " + self.eval_value(i.var) + comma
            #                                                        ~~~~~
            if n != len(args) - 1:
                # If we reached new type, like
                # type a, b, c, type2 d, e
                #               ~~~~~
                if type(i) is AST.TypedVarDefinition:
                    # Add new argument and update the type
                    curtype = self.eval_value(i.type)
                    code += curtype + " " + self.eval_value(i.var) + ", "
                else:
                    # Just add new argument
                    code += curtype + " " + self.eval_value(i) + ", "
            else:
                # Same thing here
                if type(i) is AST.TypedVarDefinition:
                    curtype = self.eval_value(i.type)
                    code += curtype + " " + self.eval_value(i.var)
                else:
                    code += curtype + " " + self.eval_value(i)
        return code

    def eval_func(self, f: AST.Func):
        """
        Build a function block
        """
        name = self.eval_value(f.name)  # Convert name to C id

        # Save our function to function list
        # FIXME: Needs to be remade to array instead of dict,
        # FIXME: because we have overloaded function and in near future - Templates/Generics
        self.funcs[name] = f

        # Funny part: Convert all argument types into a unique name
        # Needs for function overloading
        uniq = self.args2unique_name(f.args) 
        
        if name != "main":  # Make all functions unique, except `main()``
            name += uniq + "_"
        
        args = self.to_infunc_args(f.args)  # Convert Mew's arguments to C arguments
        ret  = f.ret  # Returb type of function
        ret = "void" if ret is None else self.eval_value(ret)  # Default it to void
        code = f.code  # Code

        # Function needs deallocation?
        isptr = f.need_dealloc

        # Build our building!
        head = f"{ret}{'*' if isptr else ''} {name}({args}) "
        body = CodeBuilder(self.filename, code, self.target,
                           self.incode, self.structs, f, funcs=self.funcs).start(False)

        return head + "{\n" + body + "\n}\n\n"

    def eval_if(self, f: AST.IfElse):
        """
        Build an If/Else/Else If(recursive) blocks
        """
        comp = self.eval_value(f.comparison)  # Evaluate comparison expression to C code
        # Build code for Else
        code = CodeBuilder(self.filename, f.code, self.target,
                           self.incode, self.structs, funcs=self.funcs).start(False) 

        # Wrap `else` statement to program like in `if`
        # FIXME: It's need to be lex_and_parse.py!!!
        if type(f.else_) is AST.IfElse:
            f.else_ = AST.Program([AST.Operation(f.else_, f.else_.lineno)])

        # Convert code for Else
        else_ = CodeBuilder(self.filename, f.else_, self.target,
                            self.incode, self.structs, funcs=self.funcs).start(False)

        # Let's build our building
        head = f"if({comp}) "
        body = "{\n" + code + "\n} else {" + else_ + "}\n"

        return head + body

    def eval_new(self, f: AST.New):
        """
        Builds a allocation function (we allocating with `new` operator)
        """
        # If we allocating an array
        if type(f.obj) is AST.Indexed:
            obj = self.eval_value(f.obj.var) # Get type of array we allocate
            amount = self.eval_value(f.obj.index.elements[0]) # Get amount of allocations we needed
            
            return f"__allocator_alloc(sizeof({obj}) * {amount})" # Allocate it ;)

        # Or if we allocating a structure
        obj = self.eval_value(f.obj) # Get its type
        return f"__allocator_alloc({self.sizeof_struct(obj)})"  # Allocate 1 instance of struct

    def do_operation(self, op: AST.Operation, addlines=True):
        """
        Builds ANSI C code for one operation
        """
        ev = self.eval_value(op.op)  # Evaluate a value from operation
        
        if not ev: return  # If operation is empty
        code_block = (f"// line: {op.lineno}\n" if addlines else "") + ev

        # Concatenate code of operation with a semicolon if needed
        self.code += code_block + (";\n" if code_block[-1] not in (";", "}", "\n") else "")

    def start(self, stdincs=True):
        """
        Builds ANSI C code from Mew's AST

        (Iterate over ALL operations)
        """
        for i in self.ast.operations:
            self.do_operation(i, False)  # Go through all operations without debugging lines

        pre = ""

        if stdincs:  # Add include strings if needed
            pre += f"#include \"{self.target.full_path('defs.h')}\"\n"
            pre += f"#include \"{self.target.full_path('alloc.h')}\"\n"
        pre += "\n"

        self.code = pre + self.code
            
        return self.code
