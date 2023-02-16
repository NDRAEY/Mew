from pprint import pprint
import abstract_syntax_tree as AST
from colorama import Fore

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

    def analyze(self):
        for i in self.ast.operations:
            self.analyze_part(i.op)
