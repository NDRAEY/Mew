try:
    import abstract_syntax_tree as AST
except:
    from . import abstract_syntax_tree as AST

from pprint import pprint

class CodeBuilder:
    def __init__(self, filename, ast, target, src_code):
        self.filename = filename
        self.ast = ast
        self.target = target
        self.src_code = src_code

        self.code = ""

    def build_func(self, func):
        print("Func")
        pprint(func)

        fn_ret_type = func.ret

        if fn_ret_type:
            fn_ret_type = fn_ret_type.value
        else:
            fn_ret_type = "void"

        exit(1)

    def build_operation(self, op: AST.Operation):
        op = op.op  # op op op op op op

        if type(op) is AST.ExternC:
            return op.code + "\n"
        elif type(op) is AST.End:
            return op.char
        elif type(op) is AST.Func:
            return self.build_func(op)
        else:
            print("TODO: Support for", type(op))
            exit(1)

    def build_program(self, inp: AST.Program):
        code = inp.operations

        for i in code:
            self.code += self.build_operation(i)

    def build_code(self):
        if type(self.ast) is AST.Program:
            return self.build_program(self.ast)

    def start(self):
        self.build_code()
