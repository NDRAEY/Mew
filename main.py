import lex_and_parse
from code_builder import CodeBuilder
from pprint import pprint
from analyzer import ASTAnalyzer

lexer = lex_and_parse.lex(module=lex_and_parse)
parser = lex_and_parse.yacc(debug=True, module=lex_and_parse)

if __name__=="__main__":
    """
    code = '''func fib(u32 n) {
      if n <= 1 {
        return n
      } else {
        return fib(n - 1) + fib(n - 2)
      }
    }

    fib(10)
    '''
    """

    code = '''
    u32 a = 2 + 4 + 7;
    '''

    ast = parser.parse(code)
    pprint(ast)

    analyzer = ASTAnalyzer("<stdio>", ast, code)
    analyzer.analyze()

    builder = CodeBuilder("<stdio>", ast, code)
    builder.start()

    print(builder.code)

    with open("out.c", "w") as f:
        f.write(builder.code)
        f.close()
