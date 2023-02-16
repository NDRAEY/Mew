import lex_and_parse
from pprint import pprint

if __name__=="__main__":
    lexer = lex_and_parse.lex(module=lex_and_parse)
    parser = lex_and_parse.yacc(debug=True, module=lex_and_parse)

    """
    code = '''
    func fib(u32 n) {
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
    MyStruct struc = new MyStruct();
    '''
    ast = parser.parse(code)
    
    pprint(ast)
