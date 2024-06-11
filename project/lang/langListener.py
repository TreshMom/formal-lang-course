# Generated from project/lang.g4 by ANTLR 4.13.1
from antlr4 import *

if "." in __name__:
    from .langParser import langParser
else:
    from langParser import langParser


# This class defines a complete listener for a parse tree produced by langParser.
class langListener(ParseTreeListener):

    # Enter a parse tree produced by langParser#prog.
    def enterProg(self, ctx: langParser.ProgContext):
        pass

    # Exit a parse tree produced by langParser#prog.
    def exitProg(self, ctx: langParser.ProgContext):
        pass

    # Enter a parse tree produced by langParser#stmt.
    def enterStmt(self, ctx: langParser.StmtContext):
        pass

    # Exit a parse tree produced by langParser#stmt.
    def exitStmt(self, ctx: langParser.StmtContext):
        pass

    # Enter a parse tree produced by langParser#declare.
    def enterDeclare(self, ctx: langParser.DeclareContext):
        pass

    # Exit a parse tree produced by langParser#declare.
    def exitDeclare(self, ctx: langParser.DeclareContext):
        pass

    # Enter a parse tree produced by langParser#bind.
    def enterBind(self, ctx: langParser.BindContext):
        pass

    # Exit a parse tree produced by langParser#bind.
    def exitBind(self, ctx: langParser.BindContext):
        pass

    # Enter a parse tree produced by langParser#remove.
    def enterRemove(self, ctx: langParser.RemoveContext):
        pass

    # Exit a parse tree produced by langParser#remove.
    def exitRemove(self, ctx: langParser.RemoveContext):
        pass

    # Enter a parse tree produced by langParser#add.
    def enterAdd(self, ctx: langParser.AddContext):
        pass

    # Exit a parse tree produced by langParser#add.
    def exitAdd(self, ctx: langParser.AddContext):
        pass

    # Enter a parse tree produced by langParser#expr.
    def enterExpr(self, ctx: langParser.ExprContext):
        pass

    # Exit a parse tree produced by langParser#expr.
    def exitExpr(self, ctx: langParser.ExprContext):
        pass

    # Enter a parse tree produced by langParser#set_expr.
    def enterSet_expr(self, ctx: langParser.Set_exprContext):
        pass

    # Exit a parse tree produced by langParser#set_expr.
    def exitSet_expr(self, ctx: langParser.Set_exprContext):
        pass

    # Enter a parse tree produced by langParser#edge_expr.
    def enterEdge_expr(self, ctx: langParser.Edge_exprContext):
        pass

    # Exit a parse tree produced by langParser#edge_expr.
    def exitEdge_expr(self, ctx: langParser.Edge_exprContext):
        pass

    # Enter a parse tree produced by langParser#regexp.
    def enterRegexp(self, ctx: langParser.RegexpContext):
        pass

    # Exit a parse tree produced by langParser#regexp.
    def exitRegexp(self, ctx: langParser.RegexpContext):
        pass

    # Enter a parse tree produced by langParser#range.
    def enterRange(self, ctx: langParser.RangeContext):
        pass

    # Exit a parse tree produced by langParser#range.
    def exitRange(self, ctx: langParser.RangeContext):
        pass

    # Enter a parse tree produced by langParser#select.
    def enterSelect(self, ctx: langParser.SelectContext):
        pass

    # Exit a parse tree produced by langParser#select.
    def exitSelect(self, ctx: langParser.SelectContext):
        pass

    # Enter a parse tree produced by langParser#v_filter.
    def enterV_filter(self, ctx: langParser.V_filterContext):
        pass

    # Exit a parse tree produced by langParser#v_filter.
    def exitV_filter(self, ctx: langParser.V_filterContext):
        pass


del langParser
