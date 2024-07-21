from compiler.lexer import Lexer
from compiler.tokens import *
from compiler.symbols import *
from compiler.intermediate import *
from typing import cast

class Parser:
    used: int
    lex: Lexer
    look: Token | None
    envs: list[dict[Token, Id]]
    enclosing: Stmt

    def __init__(self, l: Lexer) -> None:
        self.lex = l
        self.used = 0
        self.envs = []
        self.enclosing = Stmt.NULL
        self.move()

    def parseError(self, s: str) -> None:
        raise RuntimeError("Near line %d:\n  %s" % (self.lex.line, s))

    def move(self) -> None:
        self.look = self.lex.scan()

    def match(self, t: int | str) -> None:
        _tag = ord(t) if isinstance(t, str) else t
        if self.look.tag == _tag:
            self.move()
        else:
            self.error("Unexpected token '%s'" % str(self.look))

    def save_to_env(self, w: Token, i: Id) -> None:
        self.envs[-1][w] = i

    def get_from_env(self, w: Token) -> Id | None:
        for e in reversed(self.envs):
            if w in e.keys():
                return e[w]
        return None

    def program(self) -> None:
        s: Stmt = self.block()
        begin: int = s.new_label()
        after: int = s.new_label()
        s.emit_label(begin)
        s.gen(begin, after)
        s.emit_label(after)

    def block(self) -> Stmt:
        self.match("{")
        self.envs.append({})
        self.decls()
        s: Stmt = self.stmts()
        self.match("}")
        self.envs.pop()
        return s

    def decls(self) -> None:
        while self.look.tag == Tag.BASIC:
            p: Type = self.type()
            tok: Token = self.look
            self.match(Tag.ID)
            self.match(";")

            id = Id(cast(Word, tok), p, self.used)
            self.save_to_env(tok, id)
            self.used += p.width

    def type(self) -> Type:
        p: Type = cast(Type, self.look)
        self.match(Tag.BASIC)
        if self.look.tag != ord("["):
            return p
        else:
            return self.dims(p)

    def dims(self, p: Type) -> Type:
        self.match("[")
        tok: Token = self.look
        self.match(Tag.NUM)
        self.match("]")
        para = self.dims(p) if self.look.tag == ord("[") else p
        return Array(cast(Num, tok).value, para)

    def stmts(self) -> Stmt:
        if self.look.tag == ord("}"):
            return Stmt.NULL
        else:
            return Seq(self.stmt(), self.stmts())

    def stmt(self) -> Stmt:
        if self.look.tag == ord(";"):
            self.move()
            return Stmt.NULL
        elif self.look.tag == Tag.IF:
            self.match(Tag.IF)
            self.match("(")
            x: Expr = self.bool_expr()
            self.match(")")
            s1 = self.stmt()
            if self.look.tag != Tag.ELSE:
                return If(x, s1)
            self.match(Tag.ELSE)
            s2 = self.stmt()
            return Else(x, s1, s2)
        elif self.look.tag == Tag.WHILE:
            while_node = While()
            saved_stmt = self.enclosing
            self.enclosing = while_node
            self.match(Tag.WHILE)
            self.match("(")
            x = self.bool_expr()
            self.match(")")
            s1 = self.stmt()
            while_node.init(x, s1)
            self.enclosing = saved_stmt
            return while_node
        elif self.look.tag == Tag.DO:
            do_node = Do()
            saved_stmt = self.enclosing
            self.enclosing = do_node
            self.match(Tag.DO)
            s1 = self.stmt()
            self.match(Tag.WHILE)
            self.match("(")
            x = self.bool_expr()
            self.match(")")
            self.match(";")
            do_node.init(s1, x)
            self.enclosing = saved_stmt
            return do_node
        elif self.look.tag == Tag.BREAK:
            self.match(Tag.BREAK)
            self.match(";")
            return Break(self.enclosing)
        elif self.look.tag == ord("{"):
            return self.block()
        else:
            return self.assign()

    def assign(self) -> Expr:
        t: Token = self.look
        self.match(Tag.ID)
        id: Id | None = self.get_from_env(t)
        if id is None:
            self.parseError("'%s' undeclared." % str(t))
        if self.look.tag == ord("="):
            self.move()
            stmt = Set(id, self.bool_expr())
        else:
            x = self.offset(id)
            self.match("=")
            stmt = SetElem(x, self.bool_expr())
        self.match(";")
        return stmt

    def bool_expr(self) -> Expr:
        x = self.join_expr()
        while self.look.tag == Tag.OR:
            tok: Token = self.look
            self.move()
            x = Or(tok, x, self.join_expr())
        return x

    def join_expr(self) -> Expr:
        x = self.equality()
        while self.look.tag == Tag.AND:
            tok: Token = self.look
            self.move()
            x = And(tok, x, self.equality())
        return x

    def equality(self) -> Expr:
        x = self.rel()
        while self.look.tag in [Tag.EQ, Tag.NE]:
            tok: Token = self.look
            self.move()
            x = Rel(tok, x, self.rel())
        return x

    def rel(self) -> Expr:
        x = self.expr()
        if self.look.tag in [ord("<"), ord(">"), Tag.LE, Tag.GE]:
            tok: Token = self.look
            self.move()
            return Rel(tok, x, self.expr())
        else:
            return x

    def expr(self) -> Expr:
        x = self.term()
        while self.look.tag in [ord("+"), ord("-")]:
            tok: Token = self.look
            self.move()
            x = Arith(tok, x, self.term())
        return x

    def term(self) -> Expr:
        x = self.unary()
        while self.look.tag in [ord("*"), ord("/")]:
            tok: Token = self.look
            self.move()
            x = Arith(tok, x, self.unary())
        return x

    def unary(self) -> Expr:
        if self.look.tag == ord("-"):
            self.move()
            return Unary(Word.MINUS, self.unary())
        elif self.look.tag == ord("!"):
            tok: Token = self.look
            self.move()
            return Not(tok, self.unary())
        else:
            return self.factor()

    def factor(self) -> Expr:
        if self.look.tag == ord("("):
            self.move()
            x = self.bool_expr()
            self.match(")")
            return x
        elif self.look.tag == Tag.NUM:
            x = Constant(self.look, Type.INT)
            self.move()
            return x
        elif self.look.tag == Tag.REAL:
            x = Constant(self.look, Type.FLOAT)
            self.move()
            return x
        elif self.look.tag == Tag.TRUE:
            x = Constant.TRUE
            self.move()
            return x
        elif self.look.tag == Tag.FALSE:
            x = Constant.FALSE
            self.move()
            return x
        elif self.look.tag == Tag.ID:
            id: Id | None = self.get_from_env(self.look)
            if id is None:
                self.parseError("'%s' undeclared." % str(self.look))
            self.move()
            if self.look.tag != ord("["):
                return id
            else:
                return self.offset(id)
        else:
            self.parseError("Syntax error")

    def offset(self, id: Id) -> Access:
        id_type: Type = id.type
        self.match("[")
        index_expr = self.bool_expr()
        self.match("]")
        if not isinstance(id_type, Array):
            self.parseError("'%s' is not an array, or dimensions mismatch." % str(id))
        inner_type = cast(Array, id_type).of
        w = Constant.c_number(inner_type.width)
        t1 = Arith(Token.char("*"), index_expr, w)
        loc = t1
        while self.look.tag == ord("["):
            self.match("[")
            index_expr = self.bool_expr()
            self.match("]")
            if not isinstance(inner_type, Array):
                self.parseError("'%s' is not an array, or dimensions mismatch." % str(id))
            inner_type = cast(Array, inner_type).of
            w = Constant.c_number(inner_type.width)
            t1 = Arith(Token.char("*"), index_expr, w)
            t2 = Arith(Token.char("+"), loc, t1)
            loc = t2
        return Access(id, loc, inner_type)
