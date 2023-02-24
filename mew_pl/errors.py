try:
    from log import Log
except ImportError:
    from .log import Log

class LexerError:
    def __init__(self, lexer):
        self.lex = lexer
        self.code = lexer.lexdata

        self.lines = self.code.split("\n")
        self.lentable = list(map(lambda i: (len(i) + 1), self.lines))

    def error(self, filename, message, token):
        ln = token.lineno
        abspos = token.lexpos
        
        filemsg = f"(at {filename}:L{ln}:C{abspos})"
        Log.error(filemsg + " " + message)

        offset = Log.codeline(self.lines[ln-1], ln)

        relpos = abspos - sum(self.lentable[:ln-1])

        print(" "*(offset + relpos), "^", sep='')
