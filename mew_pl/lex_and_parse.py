try:
    from ply.yacc import yacc
    from ply.lex import lex
    import abstract_syntax_tree as AST
except ImportError:
    from .ply.lex import lex
    from .ply.yacc import yacc
    from . import abstract_syntax_tree as AST

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
t_DOT = r"\."
t_SEMICOLON = r"\;"
t_CURLY_OPEN = r"\{"
t_CURLY_CLOSE = r"\}"
t_HASH = r"\#"

reserved = (
    "IF", "ELSE", "WHILE", "FUNC", "RETURN", "NEW",
    "STRUCT", "WARNING", "EXTERN"
)

optimize_binops = False

reserved_map = {}
for r in reserved:
    reserved_map[r.lower()] = r

# r'[A-Za-z_][\w_]*'
# r'\b(?!0(x|b|o))[a-zA-Z0-9]+'

def t_ID(t):
    r'[A-Za-z_][\w_]*'
    t.type = reserved_map.get(t.value, "ID")
    return t

# t_STRING = r'"(.|\n)*?"'
t_STRING = r'"[^"\\]*(?:\\.[^"\\]*)*"'

tokens = ["STRING",
          "INTEGER",
          "PLUS", "MINUS", "MUL", "DIV",
          "ASSIGN", "EQUAL", "NOT_EQUAL",
          "GREATER", "LESS", "GREATER_EQ", "LESS_EQ",
          "DOT", "COMMA", "NEWLINE", "SEMICOLON", "HASH",
          "PAREN_OPEN", "PAREN_CLOSE",
          "CURLY_OPEN", "CURLY_CLOSE", "ID"
          ] + list(reserved)

# r'\d+'
# r'\b0((x[0-9a-fA-F_])|(b[01_])|(o[0-7_])).*'
# r"(0x[\dA-Fa-f]+|0o[0-7]+|0b[10]+|\d+)"

def t_INTEGER(token):
    r"(0x[\dA-Fa-f]+|0o[0-7]+|0b[10]+|\d+)"
    token.value = int(token.value, base=(
        16 if token.value[1]=="x" else (
            8 if token.value[1]=="o" else (
                2 if token.value[1]=="b" else (
                    10
                )
            )
        )
    ))
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
    exit(1)

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
              | if o_end
              | while o_end
              | func o_end
              | return o_end
              | typed_var o_end
              | code_block o_end
              | struct o_end
              | warn o_end
              | extern o_end
              | end
    '''
    p[0] = AST.Operation(p[1], p[1].lineno if hasattr(p[1], 'lineno') else p.lineno(1))

def p_extern_c(p):
    '''
    extern : EXTERN STRING
    '''
    p[0] = AST.ExternC(p[2][1:-1].replace("\\\"", "\""), p.lineno(1))

def p_struct(p):
    '''
    struct : STRUCT id struct_fields
    '''
    p[0] = AST.Struct(p[2], p[3], p.lineno(1))

def p_struct_fields(p):
    '''
    struct_fields : CURLY_OPEN o_newline struct_field_array o_newline CURLY_CLOSE
    '''
    p[0] = p[3]

def p_struct_field_array(p):
    '''
    struct_field_array : typeargs end
                       | struct_field_array typeargs end
    '''
    if len(p) == 3:
        p[0] = AST.StructFieldArray([p[1]])
    else:
        p[1].value.append(p[2])
        p[0] = p[1]

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
        p[0] = AST.Func(p[2], p[4], p[6], p[7], p.lineno(1), False)
    else:
        p[0] = AST.Func(p[2], AST.ParameterList([]), p[5], p[6], p.lineno(1), False)

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
    func_call : path PAREN_OPEN params PAREN_CLOSE
              | path PAREN_OPEN PAREN_CLOSE
    '''
    if len(p) == 5:
        p[0] = AST.FunctionCall(p[1], p[3], p[1].lineno)
    else:
        p[0] = AST.FunctionCall(p[1], AST.ParameterList([]), p[1].lineno)

def p_warn(p):
    '''
    warn : HASH HASH WARNING STRING NEWLINE func
    '''
    p[0] = AST.Warning(p[4], p[6], p[6].lineno)

def p_assign(p):
    '''
    assign : id ASSIGN expr
           | onetype_args ASSIGN expr
           | binop ASSIGN expr
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
        | NEW path
    '''
    p[0] = AST.New(p[2], p.lineno(1))

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
    binop : path
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

def p_path(p):
    '''
    path : value
         | path DOT value
    '''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = AST.Path([p[1], p[3]], p[1].lineno)


def p_negative_value(p):
    '''
    value : MINUS value %prec UMINUS
    '''
    if isinstance(p[2], AST.Integer):
        p[0] = AST.Integer(-p[2].value, p.lineno(2), p.lexpos(2))
    else:
        p[0] = AST.Name("-" + p[2].value, p.lineno(2), p.lexpos(2))

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
    id : ID
    '''
    p[0] = AST.Name(p[1], p.lineno(1), p.lexpos(1))

def p_value_number(p):
    '''
    value : number
    '''
    p[0] = p[1]

def p_number(p):
    '''
    number : INTEGER
    '''
    p[0] = AST.Integer(p[1], p.lineno(1), p.lexpos(1))

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
        | SEMICOLON NEWLINE
    '''
    p[0] = AST.End(p[1], p.lineno(1))

def p_empty(p):
    "empty : "
    p[0] = None

