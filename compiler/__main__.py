from compiler.lexer import Lexer
from compiler.parser import Parser
from compiler.tokens import *
from compiler.error import ParseError
import sys

if len(sys.argv) < 2:
    print("Usage: python3 -m compiler 'filename'", file=sys.stderr)

test_file = sys.argv[-1]

with open(test_file, "r", encoding="utf-8") as f:
    lexer: Lexer = Lexer(f)
    parser: Parser = Parser(lexer)
    try:
        parser.program()
        print()
        print()
        print("Memory used for allocation: %d" % parser.used)
    except ParseError as err:
        print(err, file=sys.stdout)
