"""
Lexical analyzer.
"""

from compiler.tokens import *
from compiler.symbols import *
from io import TextIOWrapper


class Lexer:
    line: int = 1

    f: TextIOWrapper
    words: dict[str, Word]
    peak: str
    line_buffer: str

    def _reserve(self, w: Word) -> None:
        self.words.update({w.lexeme: w})

    def __init__(self, f: TextIOWrapper) -> None:
        Lexer.line = 1
        self.f = f
        self.words = {}
        self.peek = " "
        self.line_buffer = ""
        self._reserve(Word("if", Tag.IF))
        self._reserve(Word("else", Tag.ELSE))
        self._reserve(Word("while", Tag.WHILE))
        self._reserve(Word("do", Tag.DO))
        self._reserve(Word("break", Tag.BREAK))
        for w in [Word.TRUE, Word.FALSE, Type.INT, Type.CHAR, Type.BOOL, Type.FLOAT]:
            self._reserve(w)

    def _read_char(self) -> None:
        self.peek = self.f.read(1)
        if self.peek != "\n":
            self.line_buffer += self.peek

    def _read_comp_char(self, c: str) -> bool:
        self._read_char()
        if self.peek != c:
            return False
        self.peek = " "
        return True

    def scan(self) -> Token | None:
        while True:
            # skips any whitespace word
            if self.peek in [" ", "\t"]:
                self._read_char()
            elif self.peek == "\n":
                Lexer.line += 1
                self.line_buffer = ""
                self._read_char()
            else:
                break

        if len(self.peek) == 0:  # EOF is encountered
            return None

        if self.peek == "&":
            if self._read_comp_char("&"):
                return Word.AND
            else:
                return Token.char("&")

        if self.peek == "|":
            if self._read_comp_char("|"):
                return Word.OR
            else:
                return Token.char("|")

        if self.peek == "=":
            if self._read_comp_char("="):
                return Word.EQ
            else:
                return Token.char("=")

        if self.peek == "!":
            if self._read_comp_char("="):
                return Word.NE
            else:
                return Token.char("!")

        if self.peek == "<":
            if self._read_comp_char("="):
                return Word.LE
            else:
                return Token.char("<")

        if self.peek == ">":
            if self._read_comp_char("="):
                return Word.GE
            else:
                return Token.char(">")

        if self.peek.isdigit():
            # An integer or float token.
            v: int = 0
            while True:
                v = 10 * v + int(self.peek)
                self._read_char()
                if not self.peek.isdigit():
                    break
            if self.peek != ".":
                return Num(v)
            # dot peeked, dealing with float token
            fl: float = v
            deg: float = 10.0
            while True:
                self._read_char()
                if not self.peek.isdigit():
                    break
                fl = fl + int(self.peek) / deg
                deg /= 10.0
            return Real(fl)

        if self.peek.isalpha():
            b: str = ""
            while True:
                b = b + self.peek
                self._read_char()
                if not self.peek.isalnum():
                    break
            if b in self.words.keys():
                return self.words[b]
            else:
                new_word = Word(b, Tag.ID)
                self.words.update({b: new_word})
                return new_word

        tok = Token.char(self.peek)
        self.peek = " "
        return tok
