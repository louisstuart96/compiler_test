class Tag:
    AND = 256
    BASIC = 257
    BREAK = 258
    DO = 259
    ELSE = 260
    EQ = 261
    FALSE = 262
    GE = 263
    ID = 264
    IF = 265
    INDEX = 266
    LE = 267
    MINUS = 268
    NE = 269
    NUM = 270
    OR = 271
    REAL = 272
    TEMP = 273
    TRUE = 274
    WHILE = 275


class Token:
    def __init__(self, tag: int) -> None:
        """
        Token constructor.

        Each single-character token is constructed by
        using character code retrieved by `ord()` method.
        """
        self.tag = tag

    @staticmethod
    def char(c: str) -> "Token":
        return Token(ord(c))

    def __str__(self) -> str:
        """
        A one-character token will be displayed
        according to its tag code (character code).

        Any other types of token will override
        `__str__()` method.
        """
        return chr(self.tag)


class Num(Token):
    def __init__(self, value: int) -> None:
        super().__init__(Tag.NUM)
        self.value = value

    def __str__(self) -> str:
        return str(self.value)


class Real(Token):
    def __init__(self, value: float) -> None:
        super().__init__(Tag.REAL)
        self.value = value

    def __str__(self) -> str:
        return str(self.value)


class Word(Token):
    def __init__(self, s: str, tag: int) -> None:
        super().__init__(tag)
        self.lexeme = s

    def __str__(self) -> str:
        return self.lexeme


Word.AND = Word("&&", Tag.AND)
Word.OR = Word("||", Tag.OR)
Word.EQ = Word("==", Tag.EQ)
Word.NE = Word("!=", Tag.NE)
Word.LE = Word("<=", Tag.LE)
Word.GE = Word(">=", Tag.GE)
Word.MINUS = Word("minus", Tag.MINUS)
Word.TRUE = Word("true", Tag.TRUE)
Word.FALSE = Word("false", Tag.FALSE)
Word.TEMP = Word("t", Tag.TEMP)
