import colorama

colorama.init()

class Log:
    @staticmethod
    def error(message):
        print(colorama.Fore.LIGHTRED_EX + "error:" + colorama.Style.RESET_ALL, message)

    @staticmethod
    def warning(message):
        print(colorama.Fore.LIGHTYELLOW_EX + "warning:" + colorama.Style.RESET_ALL, message)

    @staticmethod
    def codeline(line, lineno, offset=8):
        print(" "*offset,
              colorama.Fore.MAGENTA + str(lineno) + colorama.Style.RESET_ALL,
              "|", line)
        return len(" "*offset) + 1 + len(str(lineno)) + 3
