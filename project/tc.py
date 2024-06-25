from enum import Enum

from project.lang.langVisitor import langVisitor


class Type(Enum):
    VOID = "void"  # needed solely for the purpose of avoiding NullPointerException while printing errors
    INT = "int"
    INT_PAIR = "int*int"
    CHAR = "char"
    FA = "fa"
    RSM = "rsm"
    SET_INT = "set<int>"
    SET_INT_PAIR = "set<int*int>"
    EDGE = "edge"
    GRAPH = "graph"
    RANGE = "range"


def typecheck(expected: Type, actual: Type, message=str | None) -> None:
    if expected != actual:
        if message is None:
            raise Exception(
                f"Type mismatch error: expected type '{expected.value}', but got '{actual.value}'"
            )
        raise Exception(message)


def typecheck_any(expected: list[Type], actual: Type, message=str | None) -> None:
    if actual not in expected:
        if message is None:
            errmsg = "|".join(map(lambda x: x.value, expected))
            raise Exception(
                f"Type mismatch error: expected type '{errmsg}', but got '{actual.value}'"
            )
        raise Exception(message)


class TypeContext:
    def __init__(self):
        self.bindings = {}
        self.temp_bindings = set()  # storage of potential RSM variables not yet defined

    def bind(self, var, typ):
        if var in self.temp_bindings:
            if typ != Type.CHAR:
                typecheck_any(
                    [Type.RSM, Type.FA],
                    typ,
                    f"Variable {var} is expected to be '{Type.RSM.value}', but defined as {typ.value}",
                )
            self.bindings[var] = Type.RSM
            self.temp_bindings.remove(var)
        if typ == Type.CHAR:
            self.bindings[var] = Type.FA
        else:
            self.bindings[var] = typ

    def has_type(self, var, typ):
        if var in self.temp_bindings:
            return typ == Type.RSM
        if var in self.bindings:
            return self.bindings[var] == typ
        return False

    def lookup(self, var):
        if var in self.bindings:
            return self.bindings[var]
        else:
            self.temp_bindings.add(var)
            return Type.RSM

    def check_if_complete(self):
        if self.temp_bindings:
            for var in self.temp_bindings:
                raise Exception(f"Variable '{var}' is not defined")


class TypeCheckVisitor(langVisitor):
    def __init__(self):
        self.context = TypeContext()

    @staticmethod
    def __var_to_text(var):
        return var.symbol.text

    def visitProg(self, ctx) -> TypeContext:
        for stmt in ctx.stmt():
            self.visit(stmt)
        self.context.check_if_complete()
        return self.context

    def visitDeclare(self, ctx):
        var = ctx.VAR().getText()
        self.context.bind(var, Type.GRAPH)
        return Type.VOID

    def visitBind(self, ctx):
        var = ctx.VAR().getText()
        expr_type = self.visit(ctx.expr())
        self.context.bind(var, expr_type)
        return Type.VOID

    def visitAdd(self, ctx):
        match ctx.getChild(1).getText():
            case "vertex":
                typecheck(Type.INT, self.visit(ctx.expr()))
            case "edge":
                typecheck(Type.EDGE, self.visit(ctx.expr()))
            case _:
                raise Exception("Something definitely went wrong")

        var = ctx.VAR().getText()
        typecheck(Type.GRAPH, self.context.lookup(var))
        return Type.VOID

    def visitRemove(self, ctx):
        match ctx.getChild(1).getText():
            case "vertices":
                typecheck(Type.SET_INT, self.visit(ctx.expr()))
            case "vertex":
                typecheck(Type.INT, self.visit(ctx.expr()))
            case "edge":
                typecheck(Type.EDGE, self.visit(ctx.expr()))
            case _:
                raise Exception("Something definitely went wrong")

        var = ctx.VAR().getText()
        typecheck(Type.GRAPH, self.context.lookup(var))
        return Type.VOID

    def visitExpr(self, ctx):
        if ctx.NUM():
            return Type.INT
        elif ctx.CHAR():
            return Type.CHAR
        elif ctx.VAR():
            return self.context.lookup(ctx.VAR().getText())
        elif ctx.edge_expr():
            return self.visitEdge_expr(ctx.edge_expr())
        elif ctx.set_expr():
            return self.visitSet_expr(ctx.set_expr())
        elif ctx.regexp():
            return self.visitRegexp(ctx.regexp())
        elif ctx.select():
            return self.visitSelect(ctx.select())
        else:
            raise Exception("Unknown expression type")

    def visitEdge_expr(self, ctx):
        elem_types = [self.visit(expr) for expr in ctx.expr()]
        assert (
            len(elem_types) == 3
        ), "Something might've chanced since previous version of grammar."
        typecheck(Type.INT, elem_types[0])
        typecheck(Type.CHAR, elem_types[1])
        typecheck(Type.INT, elem_types[2])

        return Type.EDGE

    def visitSet_expr(self, ctx):
        elem_types = [self.visit(expr) for expr in ctx.expr()]
        if all(t == Type.INT for t in elem_types):
            return Type.SET_INT
        else:
            raise Exception("Set expression contains non-integer elements")

    def visitRegexp(self, ctx):
        if ctx.getChildCount() == 1:
            if ctx.CHAR():
                # Неявно оборачиваем в Symbol
                return Type.FA
            elif ctx.VAR():
                var = self.context.lookup(ctx.VAR().getText())
                typecheck_any([Type.FA, Type.RSM], var)
                return var
        elif ctx.getChildCount() == 3 and ctx.range_():
            op = ctx.getChild(1).getText()
            left = self.visit(ctx.regexp(0))
            right = self.visit(ctx.range_())
            if op == "^":
                assert left == Type.FA or left == Type.RSM
                return left
            else:
                raise Exception(
                    f"Invalid repeat operation types '{left.value}' ^ '{right.value}'"
                )
        elif ctx.getChildCount() == 3 and ctx.regexp(1):
            op = ctx.getChild(1).getText()
            left = self.visit(ctx.regexp(0))
            right = self.visit(ctx.regexp(1))
            if op == "|":
                if left == Type.FA and right == Type.FA:
                    return Type.FA
                elif (
                    (left == Type.FA and right == Type.RSM)
                    or (left == Type.RSM and right == Type.FA)
                    or (left == Type.RSM and right == Type.RSM)
                ):
                    return Type.RSM
                else:
                    raise Exception(
                        f"Invalid union operation types '{left.value}' | '{right.value}'"
                    )
            elif op == ".":
                if left == Type.FA and right == Type.FA:
                    return Type.FA
                elif (
                    (left == Type.FA and right == Type.RSM)
                    or (left == Type.RSM and right == Type.FA)
                    or (left == Type.RSM and right == Type.RSM)
                ):
                    return Type.RSM
                else:
                    raise Exception(
                        f"Invalid concatenation operation types '{left.value}' . '{right.value}'"
                    )
            elif op == "&":
                if left == Type.FA and right == Type.FA:
                    return Type.FA
                elif (left == Type.FA and right == Type.RSM) or (
                    left == Type.RSM and right == Type.FA
                ):
                    return Type.RSM
                else:
                    raise Exception(
                        f"Invalid intersection operation types '{left.value}' & '{right.value}'"
                    )
            else:
                raise Exception("Unknown operation between regexps")

        elif ctx.getChildCount() == 3 and ctx.regexp(0):
            assert (
                ctx.getChild(0).getText() == "(" and ctx.getChild(2).getText() == ")"
            ), "Код, который делает мМmмММ?!"
            return self.visit(ctx.regexp(0))

        raise Exception("Unknown regular expression type")

    def visitRange(self, ctx):
        # Так как синтаксис гарантирует, что на вход нам будут приходить только
        # Численные литералы, без переменных, то проверка на типы тут не нужна
        return Type.RANGE

    def visitSelect(self, ctx):
        # Было бы логично анализ на матч переменных вынести в отдельный visitor
        # Bсе таки это синтаксический анализ
        # Но сроки горят, жопа горит, все горит. Пока пишем так

        vf1 = ctx.v_filter(0) if ctx.v_filter(0) else None
        vf2 = ctx.v_filter(1) if ctx.v_filter(1) else None

        assert len(ctx.VAR()) in [
            4,
            5,
        ], f"If you see this message, The God abandoned this code"

        local_context = set(map(self.__var_to_text, ctx.VAR()[-3:-1]))
        if len(local_context) != 2:
            raise Exception(f"Cannot use same variable name: {list(local_context)[0]}")

        graph_var = self.__var_to_text(ctx.VAR()[-1])
        typecheck(Type.GRAPH, self.context.lookup(graph_var))

        if graph_var in local_context:
            raise Exception(
                f"Cannot use variable {ctx.VAR()[-1]} from global context as "
                f"select local variable"
            )

        if vf1:
            var = self.__var_to_text(vf1.VAR())
            if var not in local_context:
                raise Exception(f"Unknown local variable '{var}'")
            self.visit(vf1)
        if vf2:
            var = self.__var_to_text(vf2.VAR())
            if var not in local_context:
                raise Exception(f"Unknown local variable '{var}'")
            self.visit(vf2)

        q = ctx.expr()
        q_type = self.visit(q)
        # Ensure the query is of type FA or RSM
        typecheck_any(
            [Type.FA, Type.RSM],
            q_type,
            f"Invalid query type '{q_type}' in select statement",
        )

        match len(ctx.VAR()):
            case 4:
                if len(set(map(self.__var_to_text, ctx.VAR()))) > 3:
                    var1 = self.__var_to_text(ctx.VAR(0))
                    assert (
                        var1 not in local_context
                    ), "The type checker is wrong here, investigate"
                    raise Exception(f"Unknown local variable '{var1}'")
                return Type.SET_INT
            case 5:
                if len(set(map(self.__var_to_text, ctx.VAR()))) > 3:
                    var1 = self.__var_to_text(ctx.VAR(0))
                    assert (
                        var1 not in local_context
                    ), "The type checker is wrong here, investigate"
                    if var1 not in local_context:
                        raise Exception(f"Unknown local variable '{var1}'")

                    var2 = self.__var_to_text(ctx.VAR(1))
                    assert (
                        var2 not in local_context
                    ), "The type checker is wrong here, investigate"
                    if var2 not in local_context:
                        raise Exception(f"Unknown local variable '{var1}'")

                return Type.SET_INT_PAIR

        raise Exception("Something definitely went wrong")

    def visitV_filter(self, ctx):
        expr_type = self.visit(ctx.expr())
        if expr_type != Type.SET_INT:
            raise Exception("Filter expression must be of type set<int>")
        return Type.VOID
