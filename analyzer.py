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
        print(Fore.LIGHTCYAN_EX + "note: " + Fore.RESET + note)
        if fixcode:
            print(" "*8 + f"{Fore.MAGENTA}{op.lineno}{Fore.RESET} |  " + fixcode)
        exit(1)

    def warn(self, op, message, note=None, fixcode=None):
        print(Fore.LIGHTYELLOW_EX + "warning: " + Fore.RESET + \
              f"(at {self.filename}:{op.lineno}): " + \
              message)
        print(" "*8 + f"{op.lineno} | " + self.__get_line(op.lineno))
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
                    if type(op.value) is not self.typetable[type_str]:
                        self.fatal_error(op, f"An attempt to assign value of another type than declared in variable!",
                                         "Check and fix type.",
                                         self.suggest_code_init_var_type(name, op.value))
            # OK
            self.variable_table[name] = op

    def analyze(self):
        for i in self.ast.operations:
            self.analyze_part(i.op)
