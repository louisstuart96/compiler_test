from compiler.lexer import Lexer
from compiler.tokens import *
from compiler.symbols import *
from compiler.error import GrammarError


class Node:
    "Base class of nodes in syntax tree."

    labels: int = 0

    def __init__(self):
        pass

    @staticmethod
    def new_label() -> int:
        Node.labels += 1
        return Node.labels

    def error(self, s) -> None:
        raise GrammarError(s)

    def emit_label(seif, i: int) -> None:
        print("L%d:" % i, end="")

    def emit(self, s: str) -> None:
        print("\t" + s)


class Expr(Node):
    def __init__(self, op: Token, typeToken: Type) -> None:
        self.op = op
        self.type = typeToken

    def gen(self) -> "Expr":
        return self

    def reduce(self) -> "Expr":
        return self

    def emit_jumps(self, test: str, t: int, f: int) -> None:
        if t != 0 and f != 0:
            self.emit("if %s goto L%d" % (test, t))
            self.emit("goto L%d" % f)
        elif t != 0:
            self.emit("if %s goto L%d" % (test, t))
        elif f != 0:
            self.emit("iffalse %s goto L%d" % (test, f))
        else:
            pass

    def jumping(self, t: int, f: int) -> None:
        self.emit_jumps(self.__str__(), t, f)

    def __str__(self) -> str:
        return str(self.op)


class Id(Expr):
    def __init__(self, id: Word, p: Type, b: int) -> None:
        super().__init__(id, p)
        self.offset = b


class Temp(Expr):
    count: int = 0

    def __init__(self, p: Type) -> None:
        super().__init__(Word.TEMP, p)
        Temp.count += 1
        self.number = Temp.count

    def __str__(self) -> str:
        return "t%d" % self.number


class Op(Expr):
    def __init__(self, tok: Token, p: Type) -> None:
        super().__init__(tok, p)

    def reduce(self) -> Expr:
        x: Expr = self.gen()
        t: Temp = Temp(self.type)
        self.emit(str(t) + " = " + str(x))
        return t


class Arith(Op):
    def __init__(self, tok: Token, expr1: Expr, expr2: Expr) -> None:
        t = Type.max(expr1.type, expr2.type)
        if t is None:
            self.error("Type mismatch for arithmetic '%s'." % str(tok))
        super().__init__(tok, t)
        self.expr1 = expr1
        self.expr2 = expr2

    def gen(self) -> Expr:
        return Arith(self.op, self.expr1.reduce(), self.expr2.reduce())

    def __str__(self) -> str:
        return "%s %s %s" % (str(self.expr1), str(self.op), str(self.expr2))


class Unary(Op):
    def __init__(self, tok: Token, expr: Expr) -> None:
        t = Type.max(Type.INT, expr.type)
        if t is None:
            self.error("Type mismatch for unary '%s'." % str(tok))
        super().__init__(tok, t)
        self.expr = expr

    def gen(self) -> Expr:
        return Unary(self.op, self.expr.reduce())


class Constant(Expr):
    def __init__(self, tok: Token, p: Type) -> None:
        super().__init__(tok, p)

    @classmethod
    def c_number(cls, i: int) -> "Constant":
        return Constant(Num(i), Type.INT)

    def jumping(self, t: int, f: int) -> None:
        if self == Constant.TRUE and t != 0:
            self.emit("goto L %d" % t)
        if self == Constant.FALSE and f != 0:
            self.emit("goto L %d" % f)


Constant.TRUE = Constant(Word.TRUE, Type.BOOL)
Constant.FALSE = Constant(Word.FALSE, Type.BOOL)


class Logical(Expr):
    @classmethod
    def check(cls, p1: Type, p2: Type) -> Type | None:
        return Type.BOOL if p1 == Type.BOOL and p2 == Type.BOOL else None

    def __init__(self, tok: Token, expr1: Expr, expr2: Expr) -> None:
        t = self.check(expr1.type, expr2.type)
        if t is None:
            self.error("Type mismatch for logical statements.")
        super().__init__(tok, t)
        self.expr1 = expr1
        self.expr2 = expr2

    def gen(self) -> Expr:
        f = Node.new_label()
        a = Node.new_label()
        temp = Temp(self.type)
        self.jumping(0, f)
        self.emit("%s = true" % str(temp))
        self.emit("goto L%d" % a)
        self.emit_label(f)
        self.emit("%s = false" % str(temp))
        self.emit_label(a)
        return temp

    def __str__(self) -> str:
        return "%s %s %s" % (str(self.expr1), str(self.op), str(self.expr2))


class Or(Logical):
    def __init__(self, tok: Token, expr1: Expr, expr2: Expr) -> None:
        super().__init__(tok, expr1, expr2)

    def jumping(self, t: int, f: int) -> None:
        label = t if t != 0 else Node.new_label()
        self.expr1.jumping(label, 0)
        self.expr2.jumping(t, f)
        if t == 0:
            self.emit_label(label)


class And(Logical):
    def __init__(self, tok: Token, expr1: Expr, expr2: Expr) -> None:
        super().__init__(tok, expr1, expr2)

    def jumping(self, t: int, f: int) -> None:
        label = f if f != 0 else Node.new_label()
        self.expr1.jumping(0, label)
        self.expr2.jumping(t, f)
        if f == 0:
            self.emit_label(label)


class Not(Logical):
    def __init__(self, tok: Token, expr2: Expr) -> None:
        super().__init__(tok, expr2, expr2)

    def jumping(self, t: int, f: int) -> None:
        self.expr2.jumping(f, t)

    def __str__(self) -> str:
        return "%s %s" % (str(self.op), str(self.expr2))


class Rel(Logical):
    @classmethod
    def check(cls, p1: Type, p2: Type) -> Type | None:
        if isinstance(p1, Array) or isinstance(p2, Array):
            return None
        return Type.BOOL if p1 == p2 else None

    def __init__(self, tok: Token, expr1: Expr, expr2: Expr):
        super().__init__(tok, expr1, expr2)

    def jumping(self, t: int, f: int) -> None:
        a = self.expr1.reduce()
        b = self.expr2.reduce()
        test = "%s %s %s" % (str(a), str(self.op), str(b))
        self.emit_jumps(test, t, f)


class Access(Op):
    def __init__(self, a: Id, i: Expr, p: Type) -> None:
        super().__init__(Word("[]", Tag.INDEX), p)
        self.array = a
        self.index = i

    def gen(self) -> Expr:
        return Access(self.array, self.index.reduce(), self.type)

    def jumping(self, t: int, f: int) -> None:
        self.emit_jumps(str(self.reduce()), t, f)

    def __str__(self) -> str:
        return "%s[%s]" % (str(self.array), str(self.index))


class Stmt(Node):
    def __init__(self) -> None:
        self.after = 0
        super().__init__()

    def gen(self, b: int, a: int) -> None:
        pass


Stmt.NULL = Stmt()


class If(Stmt):
    def __init__(self, x: Expr, s: Stmt) -> None:
        super().__init__()
        if x.type != Type.BOOL:
            x.error("Boolean required in 'if' statement.")
        self.expr = x
        self.stmt = s

    def gen(self, b: int, a: int) -> None:
        label = Node.new_label()
        self.expr.jumping(0, a)
        self.emit_label(label)
        self.stmt.gen(label, a)


class Else(Stmt):
    def __init__(self, x: Expr, s1: Stmt, s2: Stmt) -> None:
        super().__init__()
        if x.type != Type.BOOL:
            self.error("Boolean required in 'if-else' statement.")
        self.expr = x
        self.stmt1 = s1
        self.stmt2 = s2

    def gen(self, b: int, a: int) -> None:
        label1 = Node.new_label()
        label2 = Node.new_label()
        self.expr.jumping(0, label2)
        self.emit_label(label1)
        self.stmt1.gen(label1, a)
        self.emit("goto L%d" % a)
        self.emit_label(label2)
        self.stmt2.gen(label2, a)


class While(Stmt):
    def init(self, x: Expr, s: Stmt) -> None:
        super().__init__()
        if x.type != Type.BOOL:
            self.error("Boolean required in 'while' statement.")
        self.expr = x
        self.stmt = s

    def gen(self, b: int, a: int) -> None:
        self.after = a
        self.expr.jumping(0, a)
        label = Node.new_label()
        self.emit_label(label)
        self.stmt.gen(label, b)
        self.emit("goto L%d" % b)


class Do(Stmt):
    def init(self, s: Stmt, x: Expr) -> None:
        super().__init__()
        if x.type != Type.BOOL:
            self.error("Boolean required in 'while' statement.")
        self.expr = x
        self.stmt = s

    def gen(self, b: int, a: int) -> None:
        self.after = a
        label = Node.new_label()
        self.stmt.gen(b, label)
        self.emit_label(label)
        self.expr.jumping(b, 0)


class Set(Stmt):
    @classmethod
    def check(cls, p1: Type, p2: Type) -> Type | None:
        if Type.numeric(p1) and Type.numeric(p2):
            return p2
        elif p1 == Type.BOOL and p2 == Type.BOOL:
            return p2
        else:
            return None

    def __init__(self, i: Id, x: Expr) -> None:
        super().__init__()
        if self.check(i.type, x.type) is None:
            if isinstance(i.type, Array) or isinstance(x.type, Array):
                self.error("Type error: array dimensions don't match.")
            else:
                self.error("Type error: variable doesn't match expression.")
        self.id = i
        self.expr = x

    def gen(self, b: int, a: int) -> None:
        self.emit("%s = %s" % (str(self.id), str(self.expr.gen())))


class SetElem(Stmt):
    @classmethod
    def check(cls, p1: Type, p2: Type) -> Type | None:
        if isinstance(p1, Array) or isinstance(p2, Array):
            return None
        elif p1 == p2:
            return p2
        elif Type.numeric(p1) and Type.numeric(p2):
            return p2
        else:
            return None

    def __init__(self, x: Access, y: Expr) -> None:
        super().__init__()
        if self.check(x.type, y.type) is None:
            if isinstance(x.type, Array) or isinstance(x.type, Array):
                self.error("Type error: array dimensions don't match.")
            else:
                self.error("Type error: variable doesn't match expression.")
        self.array = x.array
        self.index = x.index
        self.expr = y

    def gen(self, b: int, a: int) -> None:
        self.emit(
            "%s[%s] = %s"
            % (str(self.array), str(self.index.reduce()), str(self.expr.reduce()))
        )


class Seq(Stmt):
    def __init__(self, s1: Stmt, s2: Stmt) -> None:
        super().__init__()
        self.stmt1 = s1
        self.stmt2 = s2

    def gen(self, b: int, a: int) -> None:
        if self.stmt1 == Stmt.NULL:
            self.stmt2.gen(b, a)
        elif self.stmt2 == Stmt.NULL:
            self.stmt1.gen(b, a)
        else:
            label: int = Node.new_label()
            self.stmt1.gen(b, label)
            self.emit_label(label)
            self.stmt2.gen(label, a)


class Break(Stmt):
    def __init__(self, enclosing: Stmt) -> None:
        if enclosing == Stmt.NULL:
            self.error("Unclosed 'break' statement.")
        super().__init__()
        self.stmt = enclosing

    def gen(self, b: int, a: int) -> None:
        self.emit("goto L%d" % self.stmt.after)
