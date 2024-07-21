from compiler.lexer import Lexer
from compiler.parser import Parser
from compiler.tokens import *
import sys

if len(sys.argv) < 2:
    print("Usage: python3 -m compiler 'filename'", file=sys.stderr)

test_file = sys.argv[-1]

with open(test_file, "r", encoding="utf-8") as f:
    lexer: Lexer = Lexer(f)
    parser: Parser = Parser(lexer)
    parser.program()
    print()
    print()
    print("Memory used for allocation: %d" % parser.used)