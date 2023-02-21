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
        return self.eval_value(fc.name) + f"_({self.eval_value(fc.arguments)})"

    def eval_free(self, op):
        return f"__allocator_free({op.value});\n"

    def sizeof_type(self, typ):
        if typ in self.typesizes:
            return self.typesizes[typ]
        exit(1)

    def sizeof_struct(self, val):
        if type(val) is str:
            return self.structs[val]

        size = 0
        curtype = self.eval_value(val[0].value[0].type)
        
        for i in val:
            for j in i.value:
                if type(j) is AST.TypedVarDefinition:
                    curtype = self.eval_value(j.type)
                size += self.sizeof_type(curtype)

        return size

    def eval_sfa(self, op):
        val = op.value
        code = ""

        for i in val:
            code += self.eval_value(i) + ";\n"

        return code

    def eval_struct(self, stc):
        name = self.eval_value(stc.name)
        value = self.eval_value(stc.value)

        if name not in self.structs:
            self.structs[name] = self.sizeof_struct(stc.value.value)

        return "typedef struct " + name + " {\n" + value + "\n} " + name + ";\n\n"

    def eval_assignation(self, a):
        code = ""

        name = a.name
        val  = self.eval_value(a.value)
        ispointer = ((type(a.value) is AST.New) \
                     or ((type(a.value) is AST.FunctionCall) \
                          and self.funcs[a.value.name.value].need_dealloc
                        )
                    )

        if type(name) is AST.Path:
            return self.eval_path(name, True) + " = " + val + ";\n"
        elif type(name) is not AST.TypedVarDefinition:
            return self.eval_value(name) + " = " + val + ";\n"

        typ = self.eval_value(name.type)
        var = self.eval_value(name.var)

        code += typ + ("*" if ispointer else "") + " " + var + " = " + val + ";\n"
        self.vartable[var] = typ

        # print(f"Assigned {var} = {typ}")

        return code

    def eval_binop(self, binop: AST.BinOp):
        return  "(" + self.eval_value(binop.left) + \
                " " + binop.op + " " + \
                self.eval_value(binop.right) + ")"

    def eval_TVD(self, tvd: AST.TypedVarDefinition):
        code = ""

        typ = self.eval_value(tvd.type)
        var = tvd.var

        if type(var) is not list:
            return typ + " " + self.eval_value(var)

        for n, i in enumerate(var):
            if n != len(var)-1:
                code += typ + " " + self.eval_value(i) + ", "
            else:
                code += typ + " " + self.eval_value(i)
        return code

    def to_infunc_args(self, args):
        code = ""
        args = args.value
        if len(args) == 0: return code
        curtype = self.eval_value(args[0].type)

        for n, i in enumerate(args):
            if n != len(args) - 1:
                if type(i) is AST.TypedVarDefinition:
                    curtype = self.eval_value(i.type)
                    code += curtype + " " + self.eval_value(i.var) + ", "
                else:
                    code += curtype + " " + self.eval_value(i) + ", "
            else:
                if type(i) is AST.TypedVarDefinition:
                    curtype = self.eval_value(i.type)
                    code += curtype + " " + self.eval_value(i.var)
                else:
                    code += curtype + " " + self.eval_value(i)
        return code

    def eval_func(self, f: AST.Func):
        name = self.eval_value(f.name)

        self.funcs[name] = f

        if name != "main":
            name += "_"
        args = self.to_infunc_args(f.args)
        ret  = f.ret
        ret = "void" if ret is None else self.eval_value(ret)
        code = f.code
        isptr = f.need_dealloc

        head = f"{ret}{'*' if isptr else ''} {name}({args}) "
        body = CodeBuilder(self.filename, code, self.target,
                           self.incode, self.structs, f).start(False)

        return head + "{\n" + body + "\n}\n\n"

    def eval_if(self, f: AST.IfElse):
        comp = self.eval_value(f.comparison)
        code = CodeBuilder(self.filename, f.code, self.target,
                           self.incode, self.structs).start(False)
        
        if type(f.else_) is AST.IfElse:
            f.else_ = AST.Program([AST.Operation(f.else_, f.else_.lineno)])

        else_ = CodeBuilder(self.filename, f.else_, self.target,
                            self.incode, self.structs).start(False)

        head = f"if({comp}) "
        body = "{\n" + code + "\n} else {" + else_ + "}\n"

        return head + body

    def eval_new(self, f: AST.New):
        obj = self.eval_value(f.obj)

        return f"__allocator_alloc({self.sizeof_struct(obj)})"

    def do_operation(self, op: AST.Operation, addlines=True):
        ev = self.eval_value(op.op)
        
        if not ev: return
        code_block = (f"// line: {op.lineno}\n" if addlines else "") + ev

        self.code += code_block + (";\n" if code_block[-1] not in (";", "}", "\n") else "")

    def start(self, stdincs=True):
        for i in self.ast.operations:
            self.do_operation(i, False)

        pre = ""

        if stdincs:
            pre += f"#include \"{self.target.full_path('defs.h')}\"\n"
            pre += f"#include \"{self.target.full_path('alloc.h')}\"\n"
        pre += "\n"

        self.code = pre + self.code
            
        return self.code
