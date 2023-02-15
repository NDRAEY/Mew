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
    "IF", "ELSE", "WHILE", "FUNC", "RETURN"
)

reserved_map = {}
for r in reserved:
    reserved_map[r.lower()] = r

def t_VALUE(t):
    r'[A-Za-z_][\w_]*'
    t.type = reserved_map.get(t.value, "VALUE")
    return t

t_NAME = r'[a-zA-Z_][a-zA-Z0-9_]*'
t_STRING = r'\".*?\"'

tokens = ["STRING", "INTEGER", "NAME", 
          "PLUS", "MINUS", "MUL", "DIV",
          "ASSIGN", "EQUAL", "NOT_EQUAL",
          "GREATER", "LESS", "GREATER_EQ", "LESS_EQ",
          "COMMA", "NEWLINE", "SEMICOLON",
          "PAREN_OPEN", "PAREN_CLOSE",
          "CURLY_OPEN", "CURLY_CLOSE", "VALUE",

          "IF", "ELSE", "WHILE", "FUNC", "RETURN"]

def t_INTEGER(token):
    r"\d+"
    token.value = int(token.value)
    return token

def t_NEWLINE(token):
    r'\n'
    token.lexer.lineno += 1
    return token

def t_error(t):
    print(f'Illegal character {t.value[0]!r}')
    t.lexer.skip(1)

# Parser ================================================================

precedence = (
    ('left', 'PLUS', 'MINUS'),
    ('left', 'MUL', 'DIV'),
    ('right', 'UMINUS'),
)

def p_error(p):
    print(f'Syntax error at {p.value if p else None !r} {p.type if p else None} (:{p.lineno if p else 0})')

def p_program(p):
    '''
    program : operation
            | program operation
            | empty
    '''
    if len(p) == 2:
        p[0] = AST.Program([p[1]])
    else:
        p[1].operations.append(p[2])
        p[0] = p[1]

def p_operation(p):
    '''
    operation : assign o_end
              | binop end
              | func_call end
              | if end
              | while end
              | func end
              | value end
              | return o_end
              | end
    '''
    p[0] = AST.Operation(p[1])

def p_return(p):
    '''
    return : RETURN binop
           | RETURN
    '''
    if len(p) == 3:
        p[0] = AST.Return(p[2])
    else:
        p[0] = AST.Return(None)

def p_func(p):
    '''
    func : FUNC id PAREN_OPEN typeargs PAREN_CLOSE o_id code_block
    '''
    p[0] = AST.Func(p[2], p[4], p[6], p[7])

def p_if(p):
    '''
    if : IF binop code_block
       | IF binop code_block ELSE code_block
    '''
    if len(p) == 6:
        p[0] = AST.IfElse(p[2], p[3], p[5])
    else:
        p[0] = AST.If(p[2], p[3])

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

def p_func_call_binop(p):
    '''
    binop : func_call
    '''
    p[0] = p[1]

def p_func_call(p):
    '''
    func_call : id PAREN_OPEN params PAREN_CLOSE
              | id PAREN_OPEN PAREN_CLOSE
    '''
    if len(p) == 5:
        p[0] = AST.FunctionCall(p[1], p[3])
    else:
        p[0] = AST.FunctionCall(p[1], [])

def p_assign(p):
    '''
    assign : id ASSIGN binop
           | id id ASSIGN binop
    '''
    if len(p) == 4:
        p[0] = AST.Assignment(p[1], p[3])
    else:
        p[0] = AST.Definition(p[1], p[2], p[4])

def p_param(p):
    '''
    params : params COMMA o_newline binop
           | binop
    '''
    if len(p) == 4:
        p[1].value.append(p[3])
        p[0] = p[1]
    elif len(p) == 5:
        p[1].value.append(p[4])
        p[0] = p[1]
    else:
        p[0] = AST.ParameterList([p[1]])

def p_typeargs(p):
    '''
    typeargs : typeargs COMMA o_newline typearg
             | typearg
    '''
    if len(p) == 4:
        p[1].value.append(p[3])
        p[0] = p[1]
    elif len(p) == 5:
        p[1].value.append(p[4])
        p[0] = p[1]
    else:
        p[0] = AST.ParameterList([p[1]])


def p_typearg(p):
    '''
    typearg : id id
            | id
    '''
    if len(p) == 3:
        p[0] = [p[1], p[2]]
    else:
        p[0] = p[1]

def p_comparison_op(p):
    '''
    binop : binop LESS binop
          | binop GREATER binop
          | binop LESS_EQ binop
          | binop GREATER_EQ binop
          | binop EQUAL binop
          | binop NOT_EQUAL binop
    '''
    p[0] = AST.BinOp(p[1], p[2], p[3])

def p_binop(p):
    '''
    binop : hp_binop
          | binop PLUS binop
          | binop MINUS binop
          | binop MUL binop
          | binop DIV binop
    '''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = AST.BinOp(p[1], p[2], p[3])

def p_binop_paren(p):
    '''
    binop : PAREN_OPEN binop PAREN_CLOSE
    '''
    p[0] = p[2]

# High precendence binary operands
def p_hiprec_binop(p):
    '''
    hp_binop : value
             | hp_binop MUL hp_binop
             | hp_binop DIV hp_binop
    '''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = AST.BinOp(p[1], p[2], p[3])

def p_hiprec_binop_paren(p):
    '''
    hp_binop : PAREN_OPEN hp_binop PAREN_CLOSE
    '''
    p[0] = p[2]

def p_negative_value(p):
    '''
    value : MINUS value %prec UMINUS
    '''
    if isinstance(p[2], AST.Integer):
        p[0] = AST.Integer(-p[2].value)
    else:
        p[0] = AST.Name("-" + p[2].value)

def p_value_number(p):
    '''
    value : INTEGER
    '''
    p[0] = AST.Integer(p[1])
    
def p_value_string(p):
    '''
    value : STRING
    '''
    p[0] = AST.String(p[1])

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
    p[0] = AST.Name(p[1])

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
    p[0] = p[1]

def p_empty(p):
    "empty : "
    p[0] = None
