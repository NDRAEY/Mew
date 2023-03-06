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

        self.typetable = {
            "string": AST.String
        }

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
        print("Args")

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

    def scan_origins(self, ast):
        t = type(ast)
        
        if t is AST.Program:
            for i in ast.operations:
                self.scan_origins(i)
        elif t is AST.Operation:
            self.scan_origins(ast.op)
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

            pprint(name)
            pprint(args)

            fns = self.find_funcs(name.value)

            func = self.func_find_by_args(fns, args)

            ast.origin = func
        else:
            log.Log.error(f"TODO: Support `{t}` to scan origins of function")
            exit(1)

        print(t)

    def analyze(self):
        pprint(self.ast)
        self.scan_origins(self.ast)

        return self.ast
