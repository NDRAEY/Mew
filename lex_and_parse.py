from ply.yacc import yacc
from ply.lex import lex
import abstract_syntax_tree as AST

t_ignore = " \t"
t_PLUS = r"\+"
t_MUL = r"\*"
t_DIV = r"\/"
t_MINUS = r"\-"
t_ASSIGN = r"\="
t_EQUAL = r"\=\="
t_NOT_EQUAL = r"\!\="
t_LESS = r"\<"
t_GREATER = r"\>"
t_LESS_EQ = r"\<\="
t_GREATER_EQ = r"\>\="
t_PAREN_OPEN  = r"\("
t_PAREN_CLOSE = r"\)"
t_COMMA = r"\,"
t_SEMICOLON = r"\;"
t_CURLY_OPEN = r"\{"
t_CURLY_CLOSE = r"\}"

reserved = (
    "IF", "ELSE", "WHILE", "FUNC", "RETURN", "NEW"
)

optimize_binops = False

reserved_map = {}
for r in reserved:
    reserved_map[r.lower()] = r

def t_VALUE(t):
    r'[A-Za-z_][\w_]*'
    t.type = reserved_map.get(t.value, "VALUE")
    return t

t_NAME = r'[a-zA-Z_][a-zA-Z0-9_]*'
t_STRING = '\".*?\"'

tokens = ["STRING", "INTEGER", "NAME", 
          "PLUS", "MINUS", "MUL", "DIV",
          "ASSIGN", "EQUAL", "NOT_EQUAL",
          "GREATER", "LESS", "GREATER_EQ", "LESS_EQ",
          "COMMA", "NEWLINE", "SEMICOLON",
          "PAREN_OPEN", "PAREN_CLOSE",
          "CURLY_OPEN", "CURLY_CLOSE", "VALUE"] + list(reserved)

def t_INTEGER(token):
    r"\d+"
    token.value = int(token.value)
    return token

def t_NEWLINE(token):
    r'\n'
    token.lexer.lineno += 1
    return token

def t_comment_multi(t):
    r'/\*(.|\n)*?\*/'
    t.lexer.lineno += t.value.count('\n')

def t_comment(t):
    r'\/\/\/?.*'
    # t.lexer.lineno += 1

def t_error(t):
    print(f'Illegal character {t.value[0]!r}')
    t.lexer.skip(1)

# Parser ================================================================

def eval_partial(a, op, b):
    if op == "+":
        return a + b
    elif op == "-":
        return a - b
    elif op == "/":
        return a / b
    elif op == "*":
        return a * b

precedence = (
    ('left', 'EQUAL', 'NOT_EQUAL'),
    ('left', 'GREATER', 'LESS'),
    ('left', 'GREATER_EQ', 'LESS_EQ'),
    ('left', 'PLUS', 'MINUS'),
    ('left', 'MUL', 'DIV'),
    ('right', 'UMINUS'),
)

def p_error(p):
    errtoken = "`"+p.value+"`" if p else "`unknown`"
    tokentype = p.type if p else "`null`"
    ln = p.lineno if p else 0
    print(f'Syntax error at {errtoken} ({tokentype}) (:{ln})')

def p_program(p):
    '''
    program : operation
            | program operation
            | empty
    '''
    if len(p) == 2:
        if p[1] and not ((type(p[1]) is AST.Operation) and p[1].op == "\n"):
            p[0] = AST.Program([p[1]])
        else:
            p[0] = AST.Program([])
    else:
        p[1].operations.append(p[2])
        p[0] = p[1]

def p_operation(p):
    '''
    operation : assign o_end
              | expr o_end
              | func_call end
              | if o_end
              | while end
              | func end
              | value end
              | return o_end
              | typed_var end
              | code_block o_end
              | end
    '''
    p[0] = AST.Operation(p[1], p[1].lineno if hasattr(p[1], 'lineno') else p.lineno(1))

def p_return(p):
    '''
    return : RETURN binop
           | RETURN
    '''
    if len(p) == 3:
        p[0] = AST.Return(p[2], p.lineno(1))
    else:
        p[0] = AST.Return(None, p.lineno(1))

def p_func(p):
    '''
    func : FUNC id PAREN_OPEN typeargs PAREN_CLOSE o_id code_block
         | FUNC id PAREN_OPEN PAREN_CLOSE o_id code_block
    '''
    if len(p) == 8:
        p[0] = AST.Func(p[2], p[4], p[6], p[7], p.lineno(1))
    else:
        p[0] = AST.Func(p[2], AST.ParameterList([]), p[5], p[6], p.lineno(1))

def p_if(p):
    '''
    if : IF expr code_block
       | IF expr code_block ELSE code_block
    '''
    if len(p) == 6:
        p[0] = AST.IfElse(p[2], p[3], p[5], p.lineno(1))
    else:
        p[0] = AST.IfElse(p[2], p[3], AST.Program([]))

def p_while(p):
    '''
    while : WHILE binop code_block
    '''
    p[0] = AST.While(p[2], p[3])

def p_codeblock(p):
    '''
    code_block : CURLY_OPEN o_newline program CURLY_CLOSE
    '''
    p[0] = p[3]

def p_func_call(p):
    '''
    func_call : id PAREN_OPEN params PAREN_CLOSE
              | id PAREN_OPEN PAREN_CLOSE
    '''
    if len(p) == 5:
        p[0] = AST.FunctionCall(p[1], p[3], p[1].lineno)
    else:
        p[0] = AST.FunctionCall(p[1], [], p[1].lineno)

def p_assign(p):
    '''
    assign : id ASSIGN expr
           | onetype_args ASSIGN expr
    '''
    p[0] = AST.Assignment(p[1], p[3], p[1].lineno)

def p_param(p):
    '''
    params : params COMMA o_newline expr
           | expr
    '''
    if len(p) == 4:
        p[1].value.append(p[3])
        p[0] = p[1]
    elif len(p) == 5:
        p[1].value.append(p[4])
        p[0] = p[1]
    else:
        p[0] = AST.ParameterList([p[1]])

def p_onetyped_arglist(p):
    '''
    onetype_args : typed_var
                 | onetype_args COMMA o_newline id
    '''
    if len(p) == 5:
        p[1].var.append(p[4])
    p[0] = p[1]

def p_typeargs(p):
    '''
    typeargs  : typeargs COMMA o_newline typed_var
              | typeargs COMMA o_newline id
              | typed_var
    '''
    if len(p) == 5:
        p[1].value.append(p[4])
        p[0] = p[1]
    else:
        p[0] = AST.ParameterList([p[1]])


def p_typearg(p):
    '''
    typed_var : id id
    '''
    p[0] = AST.TypedVarDefinition(p[1], p[2], p[1].lineno)

def p_expr(p):
    '''
    expr : binop
         | new
    '''
    p[0] = p[1]

def p_new_instance(p):
    '''
    new : NEW func_call
    '''
    p[0] = AST.New(p[2])

def p_comparison_op(p):
    '''
    binop : binop LESS binop
          | binop GREATER binop
          | binop LESS_EQ binop
          | binop GREATER_EQ binop
          | binop EQUAL binop
          | binop NOT_EQUAL binop
    '''
    p[0] = AST.BinOp(p[1], p[2], p[3], p[1].lineno)

def p_binop(p):
    '''
    binop : value
          | func_call
          | binop PLUS binop
          | binop MINUS binop
          | binop MUL binop
          | binop DIV binop
    '''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = AST.BinOp(p[1], p[2], p[3], p[1].lineno)

        if optimize_binops:
            if type(p[1])==AST.Integer and type(p[3])==AST.Integer and p[2] != "/":
                p[0] = AST.Integer(eval_partial(p[1].value, p[2], p[3].value))

def p_binop_paren(p):
    '''
    binop : PAREN_OPEN binop PAREN_CLOSE
    '''
    p[0] = p[2]

def p_negative_value(p):
    '''
    value : MINUS value %prec UMINUS
    '''
    if isinstance(p[2], AST.Integer):
        p[0] = AST.Integer(-p[2].value, p.lineno(2), p.lexpos(2))
    else:
        p[0] = AST.Name("-" + p[2].value, p.lineno(2), p.lexpos(2))

def p_value_number(p):
    '''
    value : INTEGER
    '''
    p[0] = AST.Integer(p[1], p.lineno(1), p.lexpos(1))
    
def p_value_string(p):
    '''
    value : STRING
    '''
    p[0] = AST.String(p[1], p.lineno(1), p.lexpos(1))

def p_value_name(p):
    '''
    value : id
    '''
    p[0] = p[1]

def p_o_id(p):
    '''
    o_id : id
         | empty
    '''
    p[0] = p[1]

def p_id(p):
    '''
    id : NAME
       | VALUE
    '''
    p[0] = AST.Name(p[1], p.lineno(1), p.lexpos(1))

def p_optional_nl(p):
    '''
    o_newline : NEWLINE
              | empty
    '''
    p[0] = p[1]

def p_oend(p):
    '''
    o_end : end
          | empty
    '''
    p[0] = p[1]

def p_end(p):
    '''
    end : SEMICOLON
        | NEWLINE
    '''
    p[0] = AST.End(p[1], p.lineno(1))

def p_empty(p):
    "empty : "
    p[0] = None

