try:
    import abstract_syntax_tree as AST
except ImportError:
    from . import abstract_syntax_tree as AST

from colorama import Fore

class CodeBuilder:
    def __init__(self, filename, ast, string="", target="linux"):
        """
        Initializer of Code Builder that builds code from AST

        @param filename - filename of source code (need for error reporting) <--\
        @param ast - AST of source code                                         |
        @param string - If we using stdio (not file), we should pass code here -/
        """
        self.ast = ast
        self.filename = filename
        self.target = "linux"

        if string:
            self.incode = string
        else:
            with open(self.filename, "r") as f:
                self.incode = f.read()
                f.close()
    
        self.code = ""

    def __get_line(self, ln):
        if self.filename == "<stdio>":
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
        elif t is AST.End:
            return ""
        else:
            self.fatal_error(op, f"(internal) Unknown operation: {t.__name__}")

    def eval_funccall(self, fc):
        return self.eval_value(fc.name) + f"({self.eval_value(fc.arguments)})"

    def eval_assignation(self, a):
        code = ""
        name = a.name
        val  = self.eval_value(a.value)

        if type(name) is not AST.TypedVarDefinition:
            return self.eval_value(name) + " = " + val + ";"

        typ = self.eval_value(name.type)
        var = name.var

        code += typ + " " + self.eval_value(var) + " = " + val + ";\n"

        return code

    def eval_binop(self, binop):
        return "(" + self.eval_value(binop.left) + " " + binop.op + " " + self.eval_value(binop.right) + ")"

    def eval_TVD(self, tvd):
        code = ""

        typ = self.eval_value(tvd.type)
        var = tvd.var

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

    def eval_func(self, f):
        name = self.eval_value(f.name)
        args = self.to_infunc_args(f.args)
        ret  = f.ret
        ret = "void" if ret is None else self.eval_value(ret)
        code = f.code

        head = f"{ret} {name}({args}) "
        body = CodeBuilder(self.filename, code, self.incode).start()

        return head + "{\n" + body + "\n}"

    def eval_if(self, f):
        comp = self.eval_value(f.comparison)
        code = CodeBuilder(self.filename, f.code, self.incode).start()
        else_ = CodeBuilder(self.filename, f.else_, self.incode).start()

        head = f"if( {comp} ) "
        body = "{\n" + code + "\n}"

        return head + body

    def do_operation(self, op):
        ev = self.eval_value(op.op)
        
        if not ev: return
        code_block = f"// line: {op.lineno}\n" + ev

        self.code += code_block + (";\n" if code_block[-1] not in (";", "}", "\n") else "")

    def get_code_target(self, filename):
        ...

    def start(self):
        for i in self.ast.operations:
            self.do_operation(i)

        self.get_code_target("defs.h")
        return self.code
