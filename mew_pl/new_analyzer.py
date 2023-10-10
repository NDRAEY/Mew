from pprint import pprint

try:
    import log
    import utils
    import abstract_syntax_tree as AST
except ImportError:
    from . import log
    from . import utils
    from . import abstract_syntax_tree as AST

class ASTAnalyzer:
    def __init__(self, filename, ast, string=""):
        self.ast = ast
        self.funcs = []
        self.variables = {}

    def find_funcs(self, name: str):
        return [i for i in self.funcs if i.name.value == name]

    def get_type(self, typename):
        realtypename = None

        if type(typename) is AST.TypedVarDefinition:
            realtypename = typename.type.value
        else:
            print(f"get_type(): {type(typename)} is not yet supported")
            exit(1)
    
        if realtypename not in self.typetable:
            log.Log.error(f"Type `{typename}` not found")
            exit(1)
        return self.typetable[realtypename]

    def func_find_by_args(self, fns: list[AST.Func], args: list):
        argtypes = [type(i) for i in args.value]
        fntypes = [[self.get_type(j) for j in i.args.value] for i in fns]

        isok = []

        for i in fntypes:
            if len(i) == len(argtypes):
                print("All len correct")

                isok = [j is k for j, k in zip(i, argtypes)]
                break

        if not any(isok):
            print("No matching function found for call `{}`")
            exit(1)

        return fns[isok.index(True)]

    def type_check(self, ast):
        t = type(ast)

        log.Log.error("Implement type checking")
        exit(1)

        if t is AST.Program:
            for i in ast.operations:
                self.type_check(i.op)
        elif t is AST.Assignment:
            pprint(ast)
            print("Assignment")
            exit(1)
        elif t is AST.Func:
            self.type_check(ast.code)

    def scan_origins(self, ast):
        t = type(ast)
        
        if t is AST.Program:
            for i in ast.operations:
                self.scan_origins(i.op)
        elif t is AST.Func:
            # Also unpack functions
            ast.args.value = utils.unpack_func_args(ast.args.value)
            self.scan_origins(ast.code)

            self.funcs.append(ast)
        elif t is AST.ExternC:
            return
        elif t is AST.End:
            return
        elif t is AST.FunctionCall:
            name = ast.name
            args = ast.arguments

            fns = self.find_funcs(name.value)
            func = self.func_find_by_args(fns, args)

            ast.origin = func
        elif t is AST.Assignment:
            val = ast.value

            if type(val) is AST.FunctionCall:
                # If we assign a function, scan it
                self.scan_origins(val)
        elif t is AST.IfElse:
            self.scan_origins(ast.code)
        elif t is AST.Return:
            return
        else:
            log.Log.error(f"TODO: Support `{t}` to scan origins of function")
            exit(1)

    def analyze(self):
        pprint(self.ast)
        # self.type_check(self.ast)
        # self.scan_origins(self.ast)

        return self.ast
