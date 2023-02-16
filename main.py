import lex_and_parse
from code_builder import CodeBuilder
from pprint import pprint

if __name__=="__main__":
    lexer = lex_and_parse.lex(module=lex_and_parse)
    parser = lex_and_parse.yacc(debug=True, module=lex_and_parse)

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
    func a(u32 a, b, c) u32 {
        return a + b + c
    }

    func main() {
        u32 result = a(1, 2, 3);
        printf("Result: %d\\n", result);

        if result >= 4 {
            printf("Result > 4\\n");
        }else{
            printf("Result < 4\\n");
        }
    }
    '''

    ast = parser.parse(code)
    # pprint(ast)

    builder = CodeBuilder("<stdio>", ast, code)
    builder.start()

    print(builder.code)

    with open("out.c", "w") as f:
        f.write(builder.code)
        f.close()
