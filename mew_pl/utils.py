try:
    import abstract_syntax_tree as AST
except ImportError:
    from . import abstract_syntax_tree as AST

def unpack_func_args(args):
    """
    Tries to unpack args like: type a, b, c
    To unpack them like: type a, type b, type c

    (But in AST style)
    """
    if not args: return []
    curtype = args[0].type
    array = args[0].array
    total = []

    for i in args:
        if type(i) is AST.TypedVarDefinition:
            curtype = i.type
            array = i.array
            total.append(i)
        else:
            total.append(
                AST.TypedVarDefinition(
                    curtype,
                    array,
                    i,
                    i.lineno
                )
            )
    return total
