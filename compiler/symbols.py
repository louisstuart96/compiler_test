from compiler.tokens import Word, Tag


class Type(Word):
    def __init__(self, s: str, tag: int, w: int) -> None:
        super().__init__(s, tag)
        self.width = w

    def numeric(self) -> bool:
        return self == Type.INT or self == Type.CHAR or self == Type.FLOAT

    @staticmethod
    def max(p1: "Type", p2: "Type") -> "Type | None":
        if not (p1.numeric() and p2.numeric()):
            return None
        elif p1 == Type.FLOAT or p2 == Type.FLOAT:
            return Type.FLOAT
        elif p1 == Type.INT or p2 == Type.INT:
            return Type.INT
        else:
            return Type.CHAR


Type.INT = Type("int", Tag.BASIC, 4)
Type.FLOAT = Type("float", Tag.BASIC, 8)
Type.CHAR = Type("char", Tag.BASIC, 1)
Type.BOOL = Type("bool", Tag.BASIC, 1)


class Array(Type):
    def __init__(self, sz: int, p: Type) -> None:
        super().__init__("[]", Tag.INDEX, sz * p.width)
        self.size = sz
        self.of = p

    def __str__(self) -> str:
        return "[%d]%s" % (self.size, str(self.of))
