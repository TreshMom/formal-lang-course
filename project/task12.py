from networkx import MultiDiGraph
import pyformlang
from pyformlang.regular_expression import Regex
from pyformlang.finite_automaton import EpsilonNFA
from pyformlang.rsa import RecursiveAutomaton
from project import automaton
from project.lang import prog_to_tree
from project.lang.languageLexer import languageLexer
from project.lang.languageParser import languageParser
from project.lang.languageVisitor import languageVisitor


from antlr4 import *
from antlr4.InputStream import InputStream

from project.task8 import cfpq_with_tensor, ebnf_to_rsm


def get_parser(program: str) -> languageParser:
    return languageParser(CommonTokenStream(languageLexer(InputStream(program))))


void = ("void", "empty expression")


def well_formed(obj):
    return obj[0] != "void" and obj[0] != "error"


def is_valid_node_id(obj):
    return obj[0] == "num" or obj[0] == "char"


def is_valid_tag_id(obj):
    return obj[0] == "num" or obj[0] == "char"


cnt = 0


def rsm_to_ebnf(rsm: pyformlang.rsa.RecursiveAutomaton):
    global cnt
    ebnf = ""
    for _, box in rsm.boxes.items():
        ebnf += box.label.value + " -> " + str(box.dfa._get_regex_simple()) + "\n"
    cnt += 1
    new_label = "S" + str(cnt)
    ebnf = ebnf.replace(rsm.initial_label.value, new_label)
    return (ebnf, new_label)


def rsm_concatenate(
    a: pyformlang.rsa.RecursiveAutomaton, b: pyformlang.rsa.RecursiveAutomaton
):
    cfg1 = rsm_to_ebnf(a)
    cfg2 = rsm_to_ebnf(b)
    result = cfg1[0] + cfg2[0] + "S -> " + cfg1[1] + " " + cfg2[1] + "\n"
    return ("rsm", RecursiveAutomaton.from_text(result, "S"))


def rsm_union(a, b):
    cfg1 = rsm_to_ebnf(a)
    cfg2 = rsm_to_ebnf(b)
    result = cfg1[1] + cfg2[1] + "S -> " + cfg1[0] + " | " + cfg2[0] + "\n"
    return ("rsm", RecursiveAutomaton.from_text(result, "S"))


def rsm_intersect(a, b):

    if a[0] == "regex" and b[0] == "rsm":
        rsm = b[1]
        regex = a[1]
    elif a[0] == "rsm" and b[0] == "regex":
        regex = b[1]
        rsm = a[1]

    rsm = automaton.rsm_to_mat(rsm)
    regex = automaton.nfa_to_mat(regex.to_epsilon_nfa())
    intersection = automaton.intersect_automata(rsm, regex)

    return (
        "rsm",
        RecursiveAutomaton.from_regex(automaton.mat_to_nfa(intersection).to_regex()),
    )


class Visitor(languageVisitor):

    stdout = ""
    stderr = ""

    vars = {}

    def get_var(self, varname):
        if varname in self.vars:
            return self.vars[varname]
        else:
            return ("error", "var with name " + varname + " is not set")

    def get_graph_var(self, varname):
        r = self.get_var(varname)
        if not well_formed(r) or r[0] != "graph":
            return ("error", "variable " + varname + " is not graph <- " + r[1])
        return r

    def eval_expr_typed(self, expr, types):
        (e_type, e_value) = expr.accept(self)
        if e_type == "var":
            e_type, e_value = self.get_var(e_value)
        if e_type not in types:
            return (
                "error",
                "expression expected to be one of "
                + str(types)
                + ", got "
                + e_type
                + " <- "
                + str(e_value),
            )
        return (e_type, e_value)

    def __init__(self):
        pass

    # Visit a parse tree produced by languageParser#prog.
    def visitProg(self, ctx: languageParser.ProgContext):
        for i in range(ctx.getChildCount()):
            result = ctx.getChild(i).accept(self)

            if i == ctx.getChildCount() - 1:
                self.stdout += str(result) + "\n"
                return

            if result is None:
                continue
            if result[0] == "error":
                self.stderr += result[1] + "\n"
                break
            elif result[0] != "void":
                self.stdout += print_object(result)

    # Visit a parse tree produced by languageParser#stmt.

    def visitStmt(self, ctx: languageParser.StmtContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by languageParser#declare.
    def visitDeclare(self, ctx: languageParser.DeclareContext):
        self.vars[ctx.VAR().getText()] = ("graph", MultiDiGraph())
        return void

    # Visit a parse tree produced by languageParser#bind.
    def visitBind(self, ctx: languageParser.BindContext):
        result = ctx.expr().accept(self)
        if well_formed(result):
            self.vars[ctx.VAR().getText()] = result
            return void
        else:
            self.vars[ctx.VAR().getText()] = ("regex", Regex("S"))
            result = ctx.expr().accept(self)
            if well_formed(result) and result[0] == "regex":
                rsm = RecursiveAutomaton.from_regex(result[1], "S")
                # ebnf = ctx.VAR().getText() + ' -> ' + result[1]._regex
                self.vars[ctx.VAR().getText()] = ("rsm", rsm)
                return void
            else:
                return (
                    "error",
                    "binding to "
                    + ctx.VAR().getText()
                    + " failed because of invalid expression <- "
                    + result[1],
                )

    # Visit a parse tree produced by languageParser#remove.
    def visitRemove(self, ctx: languageParser.RemoveContext):
        t = ctx.children[1].getText()

        graph_ = self.get_graph_var(ctx.VAR().getText())
        if not well_formed(graph_):
            return ("error", "removed expected graph <- " + str(graph_))

        verts = None
        if t == "vertex":
            t = "vertices"
            vert = ctx.expr().accept(self)
            verts = ("set", set([vert]))
        elif t == "vertices":
            verts = ctx.expr().accept(self)

        if t == "edge":
            edge = ctx.expr().accept(self)
            if edge[0] == "edge":
                try:
                    graph_[1].remove_edge(edge[1][0][1], edge[1][2][1], edge[1][1][1])
                    return void
                except:
                    return (
                        "error",
                        "edge " + str(edge[1]) + " does not exist to be removed",
                    )

            return void

        elif t == "vertices":
            if verts[0] == "set":
                for vertex_id in verts[1]:
                    if is_valid_node_id(vertex_id):
                        try:
                            graph_[1].remove_node(vertex_id[1])
                        except:
                            return (
                                "error",
                                "node "
                                + str(vertex_id[1])
                                + " does not exist to be removed",
                            )
                    else:
                        return ("error", "malformed node id <- " + str(vertex_id))
                return void
            else:
                return ("error", "set expected for vertices argument" + str(verts))

        return ("error", "impossible parse error in remove")

    # Visit a parse tree produced by languageParser#add.
    def visitAdd(self, ctx: languageParser.AddContext):
        t = ctx.children[1].getText()

        graph_ = self.get_graph_var(ctx.VAR().getText())
        if not well_formed(graph_):
            return ("error", "add expected graph <- " + str(graph_))

        verts = None
        if t == "vertex":
            t = "vertices"
            vert = ctx.expr().accept(self)
            verts = ("set", set([vert]))
        elif t == "vertices":
            verts = ctx.expr().accept(self)

        if t == "edge":
            edge = ctx.expr().accept(self)
            if edge[0] == "edge":
                graph_[1].add_edge(edge[1][0][1], edge[1][2][1], label=edge[1][1][1])
                return void
            else:
                return ("error", "edge expected for edge argument" + str(edge))

        elif t == "vertices":
            if verts[0] == "set":
                for vertex_id in verts[1]:
                    if is_valid_node_id(vertex_id):
                        graph_[1].add_node(vertex_id[1])
                    else:
                        return ("error", "malformed node id <-" + str(vertex_id))
                return void
            else:
                return ("error", "set expected for vertices argument" + str(verts))

        return ("error", "impossible parse error in add")

    # Visit a parse tree produced by languageParser#Expr_num.
    def visitExpr_num(self, ctx: languageParser.Expr_numContext):
        return ("num", int(ctx.getText()))

    # Visit a parse tree produced by languageParser#Expr_char.
    def visitExpr_char(self, ctx: languageParser.Expr_charContext):
        return ("char", ctx.getText()[1])

    # Visit a parse tree produced by languageParser#Expr_var.
    def visitExpr_var(self, ctx: languageParser.Expr_varContext):
        return self.get_var(ctx.getText())

    # Visit a parse tree produced by languageParser#Expr_edge_expr.
    def visitExpr_edge_expr(self, ctx: languageParser.Expr_edge_exprContext):
        return ctx.edge_expr().accept(self)

    # Visit a parse tree produced by languageParser#Expr_set_expr.
    def visitExpr_set_expr(self, ctx: languageParser.Expr_set_exprContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by languageParser#Expr_regexp.
    def visitExpr_regexp(self, ctx: languageParser.Expr_regexpContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by languageParser#Expr_select.
    def visitExpr_select(self, ctx: languageParser.Expr_selectContext):
        return self.visitChildren(ctx)

    # Visit a parse tree produced by languageParser#set_expr.
    def visitSet_expr(self, ctx: languageParser.Set_exprContext):
        result = set()
        for x in ctx.expr():
            res = x.accept(self)
            if well_formed(res):
                result.add(res)
            else:
                return ("error", "malformed set because of <- " + res)
        return ("set", result)

    # Visit a parse tree produced by languageParser#edge_expr.
    def visitEdge_expr(self, ctx: languageParser.Edge_exprContext):
        u = ctx.expr(0).accept(self)
        tag = ctx.expr(1).accept(self)
        v = ctx.expr(2).accept(self)

        if is_valid_node_id(u) and is_valid_tag_id(tag) and is_valid_node_id(v):
            return ("edge", (u, tag, v))
        else:
            return (
                "error",
                "malformed edge - " + str(u) + " " + str(tag) + " " + str(v),
            )

    # Visit a parse tree produced by languageParser#Regex_braces.
    def visitRegex_braces(self, ctx: languageParser.Regex_bracesContext):
        result = ctx.regexp().accept(self)
        return result

    # Visit a parse tree produced by languageParser#Regex_dot.
    def visitRegex_concat(self, ctx: languageParser.Regex_concatContext):
        left = ctx.regexp(0).accept(self)
        right = ctx.regexp(1).accept(self)

        # print('doing concat ' + str(left) + ' ' + str(right))

        if left[0] != "error" and right[0] != "error":
            if left[0] == "regex" and right[0] == "regex":
                return ("regex", left[1].concatenate(right[1]))
            elif left[0] == "regex" and right[0] == "rsm":
                left = RecursiveAutomaton.from_regex(left[1], "S")
                right = right[1]
                return rsm_concatenate(left, right)
            elif left[0] == "rsm" and right[0] == "regex":
                left = left[1]
                right = RecursiveAutomaton.from_regex(right[1], "S")
                return rsm_concatenate(left, right)
            elif left[0] == "rsm" and right[0] == "rsm":
                return rsm_concatenate(left[1], right[1])
        return (
            "error",
            "concat says malformed inner regex/rsm <- " + str(left) + " " + str(right),
        )

    # Visit a parse tree produced by languageParser#Regex_range.
    def visitRegex_repeat(self, ctx: languageParser.Regex_repeatContext):
        left = ctx.regexp().accept(self)
        range_ = ctx.range_().accept(self)
        if left[0] != "error" and range_[0] != "error":
            from_ = range_[1][0]
            to_ = range_[1][1]

            if from_ == 0 and to_ == None:
                return ("regex", left[1].kleene_star())
            elif from_ != 0 and to_ == None:
                result = Regex("")
                for i in range(from_):
                    result = result.concatenate(left[1])
                result = result.concatenate(left[1].kleene_star())
                return ("regex", result)
            else:
                variants = Regex("")
                result = Regex("")
                for i in range(from_):
                    result = result.concatenate(left[1])
                    variants = variants.concatenate(left[1])
                for i in range(to_ - from_):
                    result = result.concatenate(left[1])
                    variants = variants.union(result)
                return ("regex", variants)

        return (
            "error",
            "can not repeat malformed regex or range <- "
            + str(left)
            + " "
            + str(range_),
        )

    # Visit a parse tree produced by languageParser#Regex_var.
    def visitRegex_var(self, ctx: languageParser.Regex_varContext):
        r = self.get_var(ctx.VAR().getText())
        if r[0] == "regex" or r[0] == "rsm":
            return r
        elif r[0] == "char":
            return ("regex", Regex(r[1]))
        return ("error", "var in regex must point to regex - " + ctx.VAR().getText())

    # Visit a parse tree produced by languageParser#Regex_and.
    def visitRegex_intersect(self, ctx: languageParser.Regex_intersectContext):
        left = ctx.regexp(0).accept(self)
        right = ctx.regexp(1).accept(self)
        if left[0] != "error" and right[0] != "error":
            if left[0] == "regex" and right[0] == "regex":
                return (
                    "regex",
                    left[1]
                    .to_epsilon_nfa()
                    .get_intersection(right[1].to_epsilon_nfa())
                    .to_regex(),
                )
            elif left[0] == "regex" and right[0] == "rsm":
                left = RecursiveAutomaton.from_regex(left[1], "S")
                right = right[1]
                return rsm_intersect(left, right)
            elif left[0] == "rsm" and right[0] == "regex":
                left = left[1]
                right = RecursiveAutomaton.from_regex(right[1], "S")
                return rsm_intersect(left, right)
        return (
            "error",
            "intersect says malformed inner regex <- " + str(left) + " " + str(right),
        )

    # Visit a parse tree produced by languageParser#Regex_or.
    def visitRegex_union(self, ctx: languageParser.Regex_unionContext):
        left = ctx.regexp(0).accept(self)
        right = ctx.regexp(1).accept(self)
        if left[0] != "error" and right[0] != "error":
            if left[0] == "regex" and right[0] == "regex":
                return ("regex", left[1].union(right[1]))
            elif left[0] == "regex" and right[0] == "rsm":
                left = RecursiveAutomaton.from_regex(left[1])
                right = right[1]
                return rsm_union(left, right)
            elif left[0] == "rsm" and right[0] == "regex":
                left = left[1]
                right = RecursiveAutomaton.from_regex(right[1])
                return rsm_union(left, right)
            elif left[0] == "rsm" and right[0] == "rsm":
                return rsm_union(left[1], right[1])
        return (
            "error",
            "union says malformed inner regex <- " + str(left) + " " + str(right),
        )

    # Visit a parse tree produced by languageParser#Regex_char.
    def visitRegex_char(self, ctx: languageParser.Regex_charContext):
        return ("regex", Regex(ctx.getText()[1]))

    # Visit a parse tree produced by languageParser#range.
    def visitRange(self, ctx: languageParser.RangeContext):
        from_ = int(ctx.NUM(0).getText())
        to_ = None
        if len(ctx.NUM()) == 2:
            to_ = int(ctx.NUM(1).getText())
        return ("range", (from_, to_))

    # Visit a parse tree produced by languageParser#select.
    def visitSelect(self, ctx: languageParser.SelectContext):
        filters = []
        for filter in ctx.v_filter():
            f_ = filter.accept(self)
            if f_[0] != "foreach":
                return ("error", "malformed filter <- " + str(f_))
            filters.append(f_)

        vars = []
        for var in ctx.VAR():
            vars.append(var.getText())

        where_var = None
        from_var = None
        in_var = None

        if len(vars) == 4:
            where_var = vars[1]
            from_var = vars[2]
            in_var = vars[3]
        else:
            where_var = vars[2]
            from_var = vars[3]
            in_var = vars[4]

        graph_ = self.get_graph_var(in_var)
        if graph_[0] != "graph":
            return ("error", "expected graph, got <- " + str(graph_))

        expr_ = ctx.expr().accept(self)
        if expr_[0] != "regex" and expr_[0] != "rsm":
            return ("error", "expected regex / rsm, got <- " + str(expr_))
        if expr_[0] == "regex":
            expr_ = ("rsm", RecursiveAutomaton.from_regex(expr_[1], "S"))

        reachable = cfpq_with_tensor(expr_[1], graph_[1])

        result = set()

        def run_one():
            where_ = self.get_var(where_var)
            from_ = self.get_var(from_var)
            expr_ = ctx.expr().accept(self)

            if (
                is_valid_node_id(where_)
                and is_valid_node_id(from_)
                and expr_[0] == "regex"
            ):
                if (from_[1], where_[1]) in reachable:
                    if len(vars) == 4:
                        return_value = self.get_var(vars[0])
                        if well_formed(return_value):
                            result.add(return_value)
                        else:
                            return (
                                "error",
                                "malformed return var <- " + str(return_value),
                            )
                    else:
                        return_value1 = self.get_var(vars[0])
                        return_value2 = self.get_var(vars[1])
                        if well_formed(return_value1) and well_formed(return_value2):
                            result.add(("tuple", (return_value1, return_value2)))
                        else:
                            return (
                                "error",
                                "malformed return vars <- "
                                + str(return_value1)
                                + " "
                                + +str(return_value2),
                            )

        if len(filters) == 0:
            run_one()
        elif len(filters) == 1:
            filter1 = filters[0]
            for x in filter1[1][1][1]:
                self.vars[filter1[1][0]] = x
                run_one()
        elif len(filters) == 2:
            filter1 = filters[0]
            filter2 = filters[1]
            for x in filter1[1][1][1]:
                self.vars[filter1[1][0]] = x
                for y in filter2[1][1][1]:
                    self.vars[filter2[1][0]] = y
                    run_one()

        return ("set", result)

    # Visit a parse tree produced by languageParser#v_filter.
    def visitV_filter(self, ctx: languageParser.V_filterContext):
        iterable = ctx.expr().accept(self)
        if iterable[0] == "set":
            return ("foreach", (ctx.VAR().getText(), iterable))
        else:
            return ("error", "malformed iterable <- " + str(iterable))


def run(program):
    (ctx, valid) = prog_to_tree(program)
    visitor = Visitor()
    if not valid:
        visitor.stdout += "Syntax error while parsing program\n"
        return
    visitor.visitProg(ctx)
    print(visitor.stdout)
    print(visitor.stderr)
    return visitor.vars


if __name__ == "__main__":

    context = run(
        """   let g is graph
            add vertex 0 to g
            add vertex 1 to g
            add vertex 2 to g
        """
    )
    assert len(context["g"][1].nodes()) == 3
    print(context["g"][1].nodes())

    context = run(
        """   let g is graph
                add vertex 0 to g
                add vertex 1 to g
                add vertex 2 to g
                add vertex 3 to g
                add vertex 4 to g
                remove vertex 4 from g
                remove vertex 1 from g
                remove vertices [0, 3, 2] from g
          """
    )
    assert len(context["g"][1].nodes()) == 0

    context = run(
        """
let g is graph

add edge (1, "a", 2) to g
add edge (2, "a", 3) to g
add edge (3, "a", 1) to g
add edge (1, "c", 5) to g
add edge (5, "b", 4) to g
add edge (4, "b", 5) to g

let q = "a"^[1..3] . q . "b"^[2..3] | "c"

let r1 = for v in [2] return u where u reachable from v in g by q

add edge (5, "d", 6) to g

let r2 = for v in [2,3] return u,v where u reachable from v in g by (q . "d")

          """
    )
    print(context["g"][1].nodes())
    assert len(context["g"][1].nodes()) == 6
