try:
    import lex_and_parse
    from code_builder import CodeBuilder
    from analyzer import ASTAnalyzer
    from targetmgr import TargetManager
except ImportError:
    from . import lex_and_parse
    from .code_builder import CodeBuilder
    from .analyzer import ASTAnalyzer
    from .targetmgr import TargetManager

from pprint import pprint
from colorama import Fore
import argparse

lexer = lex_and_parse.lex(module=lex_and_parse)
parser = lex_and_parse.yacc(debug=True, module=lex_and_parse)

target = "linux"

def main():
    """
    code = '''func fib(u32 n) u32 {
      if n <= 1 {
        return n
      } else {
        return fib(n - 1) + fib(n - 2)
      }
    }

    fib(10)
    '''
    """

    argparser = argparse.ArgumentParser(prog='mew')
    argparser.add_argument("file", nargs='?', help="File to compile")
    args = argparser.parse_args()

    if not args.file:
        print(Fore.LIGHTRED_EX+"error:"+Fore.RESET,
              "files are not specified")
        exit(1)

    target_mgr = TargetManager(target)

    code = ""
    with open(args.file, "r") as f:
        code = f.read()
        f.close()

    ast = parser.parse(code)

    analyzer = ASTAnalyzer(args.file, ast, code)
    ast = analyzer.analyze()

    pprint(ast)

    builder = CodeBuilder(args.file, ast, target_mgr, code)
    builder.start()

    print(builder.code)

    with open("out.c", "w") as f:
        f.write(builder.code)
        f.close()

if __name__=="__main__":
    main()
